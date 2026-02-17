// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title VoterRegistry
 * @dev Manages voter registration and eligibility for elections
 * Stores voter records with hashed identities for privacy
 */
contract VoterRegistry is Ownable {
    struct VoterRecord {
        bool isRegistered;
        bool hasVoted;
        uint256 constituencyId;
        uint256 registeredAt;
        uint256 votedAt;
    }

    // Mapping: voterHash => VoterRecord
    mapping(bytes32 => VoterRecord) private voters;

    // Constituency statistics
    mapping(uint256 => uint256) public constituencyRegisteredCount;
    mapping(uint256 => uint256) public constituencyVotedCount;

    // Global statistics
    uint256 public totalRegistered;
    uint256 public totalVoted;
    bool public registrationOpen;

    // Authorized contracts that can mark voters as voted
    address public electionController;

    // Events
    event VoterRegistered(bytes32 indexed voterHash, uint256 indexed constituencyId, uint256 timestamp);
    event VoterMarkedVoted(bytes32 indexed voterHash, uint256 timestamp);
    event RegistrationStatusChanged(bool isOpen);
    event ElectionControllerSet(address indexed controller);

    /**
     * @dev Constructor sets initial owner and opens registration
     * @param initialController Initial election controller address
     */
    constructor(address initialController) Ownable(msg.sender) {
        registrationOpen = true;
        electionController = initialController;
    }

    /**
     * @dev Modifier to restrict access to owner or authorized controller
     */
    modifier onlyAuthorized() {
        require(
            msg.sender == owner() || msg.sender == electionController,
            "VoterRegistry: caller is not authorized"
        );
        _;
    }

    /**
     * @dev Set the election controller address
     * @param _controller Address of the election controller
     */
    function setElectionController(address _controller) external onlyOwner {
        require(_controller != address(0), "VoterRegistry: controller cannot be zero address");
        electionController = _controller;
        emit ElectionControllerSet(_controller);
    }

    /**
     * @dev Register a new voter with hashed identity
     * @param voterHash Keccak256 hash of voter identity
     * @param constituencyId Constituency ID the voter belongs to
     */
    function registerVoter(bytes32 voterHash, uint256 constituencyId) external onlyOwner {
        require(registrationOpen, "VoterRegistry: registration is closed");
        require(voterHash != bytes32(0), "VoterRegistry: invalid voter hash");
        require(!voters[voterHash].isRegistered, "VoterRegistry: voter already registered");

        voters[voterHash] = VoterRecord({
            isRegistered: true,
            hasVoted: false,
            constituencyId: constituencyId,
            registeredAt: block.timestamp,
            votedAt: 0
        });

        totalRegistered++;
        constituencyRegisteredCount[constituencyId]++;

        emit VoterRegistered(voterHash, constituencyId, block.timestamp);
    }

    /**
     * @dev Mark a voter as having voted
     * @param voterHash Keccak256 hash of voter identity
     */
    function markVoted(bytes32 voterHash) external onlyAuthorized {
        require(voters[voterHash].isRegistered, "VoterRegistry: voter not registered");
        require(!voters[voterHash].hasVoted, "VoterRegistry: voter has already voted");

        voters[voterHash].hasVoted = true;
        voters[voterHash].votedAt = block.timestamp;

        totalVoted++;
        constituencyVotedCount[voters[voterHash].constituencyId]++;

        emit VoterMarkedVoted(voterHash, block.timestamp);
    }

    /**
     * @dev Check if a voter is eligible to vote
     * @param voterHash Keccak256 hash of voter identity
     * @return bool True if voter is registered and has not voted
     */
    function isEligible(bytes32 voterHash) external view returns (bool) {
        return voters[voterHash].isRegistered && !voters[voterHash].hasVoted;
    }

    /**
     * @dev Get complete voter record
     * @param voterHash Keccak256 hash of voter identity
     * @return VoterRecord struct
     */
    function getVoterRecord(bytes32 voterHash) external view returns (VoterRecord memory) {
        return voters[voterHash];
    }

    /**
     * @dev Get constituency statistics
     * @param constituencyId Constituency ID
     * @return registered Number of registered voters
     * @return voted Number of voters who have voted
     */
    function getConstituencyStats(uint256 constituencyId)
        external
        view
        returns (uint256 registered, uint256 voted)
    {
        return (
            constituencyRegisteredCount[constituencyId],
            constituencyVotedCount[constituencyId]
        );
    }

    /**
     * @dev Set registration status
     * @param isOpen True to open registration, false to close
     */
    function setRegistrationStatus(bool isOpen) external onlyOwner {
        registrationOpen = isOpen;
        emit RegistrationStatusChanged(isOpen);
    }

    /**
     * @dev Close registration (convenience function)
     */
    function closeRegistration() external onlyOwner {
        registrationOpen = false;
        emit RegistrationStatusChanged(false);
    }

    /**
     * @dev Get global voting statistics
     * @return _totalRegistered Total registered voters
     * @return _totalVoted Total voters who have voted
     * @return turnoutBasisPoints Turnout percentage in basis points (e.g., 6500 = 65.00%)
     */
    function getGlobalStats()
        external
        view
        returns (
            uint256 _totalRegistered,
            uint256 _totalVoted,
            uint256 turnoutBasisPoints
        )
    {
        _totalRegistered = totalRegistered;
        _totalVoted = totalVoted;

        if (_totalRegistered > 0) {
            turnoutBasisPoints = (_totalVoted * 10000) / _totalRegistered;
        } else {
            turnoutBasisPoints = 0;
        }

        return (_totalRegistered, _totalVoted, turnoutBasisPoints);
    }
}
