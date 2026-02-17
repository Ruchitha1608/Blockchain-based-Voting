// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "./VoterRegistry.sol";
import "./VotingBooth.sol";
import "./ResultsTallier.sol";

/**
 * @title ElectionController
 * @dev Main controller for election lifecycle with strict phase management
 * Coordinates VoterRegistry, VotingBooth, and ResultsTallier
 */
contract ElectionController is Ownable {
    enum ElectionPhase {
        Setup,      // Initial phase: registering voters and candidates
        Ready,      // Configuration complete, ready to start
        Active,     // Voting is open
        Closed,     // Voting has closed, ready for tallying
        Finalized   // Results tallied and finalized
    }

    // Contract references
    VoterRegistry public voterRegistry;
    VotingBooth public votingBooth;
    ResultsTallier public resultsTallier;

    // Election state
    ElectionPhase public currentPhase;
    uint256 public electionId;
    string public electionName;

    // Timing
    uint256 public setupCompletedAt;
    uint256 public votingStartedAt;
    uint256 public votingClosedAt;
    uint256 public resultsFinalizedAt;

    // Events
    event PhaseChanged(ElectionPhase indexed newPhase, uint256 timestamp);
    event VoterRegisteredViaController(bytes32 indexed voterHash, uint256 constituencyId);
    event CandidateRegisteredViaController(uint256 indexed candidateId, uint256 constituencyId);
    event VoteSubmittedViaController(uint256 indexed candidateId, uint256 constituencyId);
    event ElectionStarted(uint256 startTime, uint256 endTime);
    event ElectionClosed(uint256 closeTime);
    event ResultsTalliedAndFinalized(uint256 timestamp);

    /**
     * @dev Constructor
     * @param _electionId Unique election identifier
     * @param _electionName Human-readable election name
     * @param _voterRegistry Address of VoterRegistry contract
     * @param _votingBooth Address of VotingBooth contract
     * @param _resultsTallier Address of ResultsTallier contract
     */
    constructor(
        uint256 _electionId,
        string memory _electionName,
        address _voterRegistry,
        address _votingBooth,
        address _resultsTallier
    ) Ownable(msg.sender) {
        require(_voterRegistry != address(0), "ElectionController: invalid registry address");
        require(_votingBooth != address(0), "ElectionController: invalid booth address");
        require(_resultsTallier != address(0), "ElectionController: invalid tallier address");

        electionId = _electionId;
        electionName = _electionName;
        voterRegistry = VoterRegistry(_voterRegistry);
        votingBooth = VotingBooth(_votingBooth);
        resultsTallier = ResultsTallier(_resultsTallier);

        currentPhase = ElectionPhase.Setup;
    }

    /**
     * @dev Modifier to ensure current phase matches required phase
     */
    modifier inPhase(ElectionPhase requiredPhase) {
        require(
            currentPhase == requiredPhase,
            string(abi.encodePacked(
                "ElectionController: not in required phase. Current: ",
                uint2str(uint256(currentPhase)),
                ", Required: ",
                uint2str(uint256(requiredPhase))
            ))
        );
        _;
    }

    /**
     * @dev Register a voter (only in Setup phase)
     * @param voterHash Keccak256 hash of voter identity
     * @param constituencyId Constituency ID
     */
    function registerVoter(bytes32 voterHash, uint256 constituencyId)
        external
        onlyOwner
        inPhase(ElectionPhase.Setup)
    {
        voterRegistry.registerVoter(voterHash, constituencyId);
        emit VoterRegisteredViaController(voterHash, constituencyId);
    }

    /**
     * @dev Register a candidate (only in Setup phase)
     * @param candidateId Candidate identifier
     * @param constituencyId Constituency ID
     */
    function registerCandidate(uint256 candidateId, uint256 constituencyId)
        external
        onlyOwner
        inPhase(ElectionPhase.Setup)
    {
        votingBooth.registerCandidate(candidateId, constituencyId);
        emit CandidateRegisteredViaController(candidateId, constituencyId);
    }

    /**
     * @dev Batch register candidates (only in Setup phase)
     * @param candidateIds Array of candidate IDs
     * @param constituencyIds Array of constituency IDs
     */
    function batchRegisterCandidates(
        uint256[] calldata candidateIds,
        uint256[] calldata constituencyIds
    ) external onlyOwner inPhase(ElectionPhase.Setup) {
        votingBooth.batchRegisterCandidates(candidateIds, constituencyIds);

        for (uint256 i = 0; i < candidateIds.length; i++) {
            emit CandidateRegisteredViaController(candidateIds[i], constituencyIds[i]);
        }
    }

    /**
     * @dev Mark setup as complete and transition to Ready phase
     */
    function completeSetup() external onlyOwner inPhase(ElectionPhase.Setup) {
        // Close voter registration
        voterRegistry.closeRegistration();

        setupCompletedAt = block.timestamp;
        currentPhase = ElectionPhase.Ready;

        emit PhaseChanged(ElectionPhase.Ready, block.timestamp);
    }

    /**
     * @dev Start the election (transition from Ready to Active)
     * @param startTime Unix timestamp when voting starts
     * @param endTime Unix timestamp when voting ends
     */
    function startElection(uint256 startTime, uint256 endTime)
        external
        onlyOwner
        inPhase(ElectionPhase.Ready)
    {
        require(endTime > startTime, "ElectionController: invalid time range");
        require(startTime >= block.timestamp, "ElectionController: start time must be in future");

        // Open voting in the booth
        votingBooth.openVoting(startTime, endTime);

        votingStartedAt = block.timestamp;
        currentPhase = ElectionPhase.Active;

        emit ElectionStarted(startTime, endTime);
        emit PhaseChanged(ElectionPhase.Active, block.timestamp);
    }

    /**
     * @dev Submit a vote (only in Active phase)
     * @param voterHash Keccak256 hash of voter identity
     * @param candidateId Candidate identifier
     * @param constituencyId Constituency identifier
     */
    function submitVote(
        bytes32 voterHash,
        uint256 candidateId,
        uint256 constituencyId
    ) external inPhase(ElectionPhase.Active) {
        votingBooth.castVote(voterHash, candidateId, constituencyId);
        emit VoteSubmittedViaController(candidateId, constituencyId);
    }

    /**
     * @dev Close the election (transition from Active to Closed)
     */
    function closeElection() external onlyOwner inPhase(ElectionPhase.Active) {
        votingBooth.closeVoting();

        votingClosedAt = block.timestamp;
        currentPhase = ElectionPhase.Closed;

        emit ElectionClosed(block.timestamp);
        emit PhaseChanged(ElectionPhase.Closed, block.timestamp);
    }

    /**
     * @dev Tally results and finalize (transition from Closed to Finalized)
     * @param constituencyIds Array of all constituency IDs
     * @param candidateIdsPerConstituency 2D array of candidate IDs for each constituency
     * @param expectedVotesPerConstituency Array of expected vote counts for validation
     */
    function tallyAndFinalize(
        uint256[] calldata constituencyIds,
        uint256[][] calldata candidateIdsPerConstituency,
        uint256[] calldata expectedVotesPerConstituency
    ) external onlyOwner inPhase(ElectionPhase.Closed) {
        require(
            constituencyIds.length == candidateIdsPerConstituency.length,
            "ElectionController: array length mismatch"
        );
        require(
            constituencyIds.length == expectedVotesPerConstituency.length,
            "ElectionController: expected votes array length mismatch"
        );

        // Tally each constituency
        for (uint256 i = 0; i < constituencyIds.length; i++) {
            resultsTallier.tallyConstituency(
                constituencyIds[i],
                candidateIdsPerConstituency[i],
                expectedVotesPerConstituency[i]
            );
        }

        // Finalize results
        resultsTallier.finalizeResults();

        resultsFinalizedAt = block.timestamp;
        currentPhase = ElectionPhase.Finalized;

        emit ResultsTalliedAndFinalized(block.timestamp);
        emit PhaseChanged(ElectionPhase.Finalized, block.timestamp);
    }

    /**
     * @dev Get current phase as string
     * @return string Phase name
     */
    function getCurrentPhase() external view returns (string memory) {
        if (currentPhase == ElectionPhase.Setup) return "Setup";
        if (currentPhase == ElectionPhase.Ready) return "Ready";
        if (currentPhase == ElectionPhase.Active) return "Active";
        if (currentPhase == ElectionPhase.Closed) return "Closed";
        if (currentPhase == ElectionPhase.Finalized) return "Finalized";
        return "Unknown";
    }

    /**
     * @dev Check if voting is currently open
     * @return bool True if in Active phase and within voting window
     */
    function isVotingOpen() external view returns (bool) {
        if (currentPhase != ElectionPhase.Active) {
            return false;
        }

        (bool isOpen, uint256 startTime, uint256 endTime, uint256 currentTime) =
            votingBooth.getVotingStatus();

        return isOpen && currentTime >= startTime && currentTime <= endTime;
    }

    /**
     * @dev Get comprehensive election summary
     * @return _electionId The election ID
     * @return _electionName The election name
     * @return phase Current election phase as string
     * @return totalRegistered Total number of registered voters
     * @return totalVoted Total number of votes cast
     * @return turnoutBasisPoints Voter turnout in basis points
     * @return votingIsOpen Whether voting is currently open
     * @return resultsAreFinalized Whether results have been finalized
     */
    function getElectionSummary()
        external
        view
        returns (
            uint256 _electionId,
            string memory _electionName,
            string memory phase,
            uint256 totalRegistered,
            uint256 totalVoted,
            uint256 turnoutBasisPoints,
            bool votingIsOpen,
            bool resultsAreFinalized
        )
    {
        _electionId = electionId;
        _electionName = electionName;

        if (currentPhase == ElectionPhase.Setup) phase = "Setup";
        else if (currentPhase == ElectionPhase.Ready) phase = "Ready";
        else if (currentPhase == ElectionPhase.Active) phase = "Active";
        else if (currentPhase == ElectionPhase.Closed) phase = "Closed";
        else if (currentPhase == ElectionPhase.Finalized) phase = "Finalized";

        (totalRegistered, totalVoted, turnoutBasisPoints) = voterRegistry.getGlobalStats();

        (bool isOpen, , , ) = votingBooth.getVotingStatus();
        votingIsOpen = isOpen && (currentPhase == ElectionPhase.Active);

        (resultsAreFinalized, ) = resultsTallier.getFinalizationStatus();

        return (
            _electionId,
            _electionName,
            phase,
            totalRegistered,
            totalVoted,
            turnoutBasisPoints,
            votingIsOpen,
            resultsAreFinalized
        );
    }

    /**
     * @dev Get phase transition timestamps
     * @return _setupCompletedAt Timestamp when setup phase was completed
     * @return _votingStartedAt Timestamp when voting started
     * @return _votingClosedAt Timestamp when voting was closed
     * @return _resultsFinalizedAt Timestamp when results were finalized
     */
    function getPhaseTimestamps()
        external
        view
        returns (
            uint256 _setupCompletedAt,
            uint256 _votingStartedAt,
            uint256 _votingClosedAt,
            uint256 _resultsFinalizedAt
        )
    {
        return (
            setupCompletedAt,
            votingStartedAt,
            votingClosedAt,
            resultsFinalizedAt
        );
    }

    /**
     * @dev Helper function to convert uint to string
     */
    function uint2str(uint256 _i) internal pure returns (string memory) {
        if (_i == 0) {
            return "0";
        }
        uint256 j = _i;
        uint256 length;
        while (j != 0) {
            length++;
            j /= 10;
        }
        bytes memory bstr = new bytes(length);
        uint256 k = length;
        while (_i != 0) {
            k = k - 1;
            uint8 temp = (48 + uint8(_i - _i / 10 * 10));
            bytes1 b1 = bytes1(temp);
            bstr[k] = b1;
            _i /= 10;
        }
        return string(bstr);
    }
}
