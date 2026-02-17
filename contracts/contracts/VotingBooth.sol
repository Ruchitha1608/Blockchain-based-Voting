// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "./VoterRegistry.sol";

/**
 * @title VotingBooth
 * @dev Handles the voting process with privacy protections
 * Vote records are private to maintain ballot secrecy
 */
contract VotingBooth is Ownable {
    struct VoteRecord {
        uint256 candidateId;
        uint256 constituencyId;
        uint256 timestamp;
        uint256 blockNumber;
    }

    // PRIVATE: Mapping of voterHash to their vote (maintains privacy)
    mapping(bytes32 => VoteRecord) private voteRecords;

    // PRIVATE: Vote counts per candidate (hidden until voting closes)
    mapping(uint256 => uint256) private voteCounts;

    // Track if voter has submitted (prevents double voting)
    mapping(bytes32 => bool) private hasSubmitted;

    // Candidate validation: constituencyId => candidateId => isValid
    mapping(uint256 => mapping(uint256 => bool)) public validCandidates;

    // Election state
    bool public votingOpen;
    uint256 public votingStartTime;
    uint256 public votingEndTime;
    uint256 public electionId;

    // Reference to voter registry
    VoterRegistry public voterRegistry;

    // Events - NOTE: voterHash is NOT emitted to protect privacy
    event VoteCast(
        uint256 indexed candidateId,
        uint256 indexed constituencyId,
        uint256 blockNumber,
        uint256 timestamp
    );
    event CandidateRegistered(uint256 indexed candidateId, uint256 indexed constituencyId);
    event VotingOpened(uint256 startTime, uint256 endTime);
    event VotingClosed(uint256 closeTime);

    /**
     * @dev Constructor
     * @param _voterRegistry Address of the VoterRegistry contract
     * @param _electionId Unique identifier for this election
     */
    constructor(address _voterRegistry, uint256 _electionId) Ownable(msg.sender) {
        require(_voterRegistry != address(0), "VotingBooth: invalid registry address");
        voterRegistry = VoterRegistry(_voterRegistry);
        electionId = _electionId;
        votingOpen = false;
    }

    /**
     * @dev Modifier to ensure voting is open
     */
    modifier onlyWhenVotingOpen() {
        require(votingOpen, "VotingBooth: voting is not open");
        require(block.timestamp >= votingStartTime, "VotingBooth: voting has not started");
        require(block.timestamp <= votingEndTime, "VotingBooth: voting has ended");
        _;
    }

    /**
     * @dev Modifier to ensure voting is closed
     */
    modifier onlyWhenVotingClosed() {
        require(!votingOpen, "VotingBooth: voting is still open");
        _;
    }

    /**
     * @dev Register a candidate for a constituency
     * @param candidateId Unique candidate identifier
     * @param constituencyId Constituency the candidate is running in
     */
    function registerCandidate(uint256 candidateId, uint256 constituencyId) external onlyOwner {
        require(!votingOpen, "VotingBooth: cannot register candidates while voting is open");
        require(candidateId > 0, "VotingBooth: invalid candidate ID");
        require(!validCandidates[constituencyId][candidateId], "VotingBooth: candidate already registered");

        validCandidates[constituencyId][candidateId] = true;
        emit CandidateRegistered(candidateId, constituencyId);
    }

    /**
     * @dev Open voting for a specified period
     * @param startTime Unix timestamp when voting starts
     * @param endTime Unix timestamp when voting ends
     */
    function openVoting(uint256 startTime, uint256 endTime) external onlyOwner {
        require(!votingOpen, "VotingBooth: voting is already open");
        require(endTime > startTime, "VotingBooth: invalid time range");
        require(startTime >= block.timestamp, "VotingBooth: start time must be in the future");

        votingOpen = true;
        votingStartTime = startTime;
        votingEndTime = endTime;

        emit VotingOpened(startTime, endTime);
    }

    /**
     * @dev Close voting (can be called early by owner if needed)
     */
    function closeVoting() external onlyOwner {
        require(votingOpen, "VotingBooth: voting is not open");
        votingOpen = false;
        emit VotingClosed(block.timestamp);
    }

    /**
     * @dev Cast a vote
     * @param voterHash Keccak256 hash of voter identity
     * @param candidateId ID of the candidate to vote for
     * @param constituencyId Constituency ID of the voter
     */
    function castVote(
        bytes32 voterHash,
        uint256 candidateId,
        uint256 constituencyId
    ) external onlyWhenVotingOpen {
        // Check voter eligibility through registry
        require(
            voterRegistry.isEligible(voterHash),
            "VotingBooth: voter not eligible"
        );

        // Check voter hasn't already submitted in this contract
        require(
            !hasSubmitted[voterHash],
            "VotingBooth: voter has already submitted vote"
        );

        // Validate candidate is registered for this constituency
        require(
            validCandidates[constituencyId][candidateId],
            "VotingBooth: invalid candidate for constituency"
        );

        // Record the vote (private)
        voteRecords[voterHash] = VoteRecord({
            candidateId: candidateId,
            constituencyId: constituencyId,
            timestamp: block.timestamp,
            blockNumber: block.number
        });

        // Mark as submitted
        hasSubmitted[voterHash] = true;

        // Increment vote count (private)
        voteCounts[candidateId]++;

        // Mark voter as voted in registry
        voterRegistry.markVoted(voterHash);

        // Emit event WITHOUT voterHash to protect privacy
        emit VoteCast(candidateId, constituencyId, block.number, block.timestamp);
    }

    /**
     * @dev Get vote count for a candidate (only after voting closes)
     * @param candidateId Candidate identifier
     * @return uint256 Number of votes received
     */
    function getVoteCount(uint256 candidateId)
        external
        view
        onlyWhenVotingClosed
        returns (uint256)
    {
        return voteCounts[candidateId];
    }

    /**
     * @dev Check if a voter has submitted a vote
     * @param voterHash Keccak256 hash of voter identity
     * @return bool True if voter has submitted
     */
    function voterHasSubmitted(bytes32 voterHash) external view returns (bool) {
        return hasSubmitted[voterHash];
    }

    /**
     * @dev Check if a candidate is valid for a constituency
     * @param constituencyId Constituency identifier
     * @param candidateId Candidate identifier
     * @return bool True if candidate is registered for this constituency
     */
    function isCandidateValid(uint256 constituencyId, uint256 candidateId)
        external
        view
        returns (bool)
    {
        return validCandidates[constituencyId][candidateId];
    }

    /**
     * @dev Get voting status and timing
     * @return isOpen Whether voting is currently open
     * @return startTime Voting start timestamp
     * @return endTime Voting end timestamp
     * @return currentTime Current block timestamp
     */
    function getVotingStatus()
        external
        view
        returns (
            bool isOpen,
            uint256 startTime,
            uint256 endTime,
            uint256 currentTime
        )
    {
        return (votingOpen, votingStartTime, votingEndTime, block.timestamp);
    }

    /**
     * @dev Batch register multiple candidates (gas optimization)
     * @param candidateIds Array of candidate IDs
     * @param constituencyIds Array of corresponding constituency IDs
     */
    function batchRegisterCandidates(
        uint256[] calldata candidateIds,
        uint256[] calldata constituencyIds
    ) external onlyOwner {
        require(!votingOpen, "VotingBooth: cannot register candidates while voting is open");
        require(
            candidateIds.length == constituencyIds.length,
            "VotingBooth: array length mismatch"
        );

        for (uint256 i = 0; i < candidateIds.length; i++) {
            uint256 candidateId = candidateIds[i];
            uint256 constituencyId = constituencyIds[i];

            require(candidateId > 0, "VotingBooth: invalid candidate ID");
            require(
                !validCandidates[constituencyId][candidateId],
                "VotingBooth: candidate already registered"
            );

            validCandidates[constituencyId][candidateId] = true;
            emit CandidateRegistered(candidateId, constituencyId);
        }
    }
}
