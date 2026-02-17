// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "./VotingBooth.sol";

/**
 * @title ResultsTallier
 * @dev Tallies election results and handles tie detection
 * Results are only available after finalization
 */
contract ResultsTallier is Ownable {
    struct ConstituencyResult {
        uint256 constituencyId;
        uint256 winnerCandidateId;
        uint256 winnerVoteCount;
        bool isTied;
        uint256 totalVotes;
        bool isFinalized;
        uint256 finalizedAt;
    }

    struct CandidateResult {
        uint256 candidateId;
        uint256 voteCount;
        uint256 constituencyId;
    }

    // Reference to voting booth
    VotingBooth public votingBooth;

    // Results storage
    mapping(uint256 => ConstituencyResult) private constituencyResults;
    mapping(uint256 => CandidateResult) private candidateResults;

    // Track which constituencies have been tallied
    mapping(uint256 => bool) public constituencyTallied;

    // Global finalization status
    bool public resultsFinalized;
    uint256 public finalizedAt;

    // Events
    event ConstituencyTallied(
        uint256 indexed constituencyId,
        uint256 winnerCandidateId,
        uint256 voteCount,
        bool isTied
    );
    event TieDetected(uint256 indexed constituencyId, uint256 tiedVoteCount);
    event ResultsFinalized(uint256 timestamp);
    event WinnerDeclared(
        uint256 indexed constituencyId,
        uint256 indexed candidateId,
        uint256 voteCount
    );

    /**
     * @dev Constructor
     * @param _votingBooth Address of the VotingBooth contract
     */
    constructor(address _votingBooth) Ownable(msg.sender) {
        require(_votingBooth != address(0), "ResultsTallier: invalid voting booth address");
        votingBooth = VotingBooth(_votingBooth);
        resultsFinalized = false;
    }

    /**
     * @dev Modifier to ensure results are finalized before viewing
     */
    modifier onlyWhenFinalized() {
        require(resultsFinalized, "ResultsTallier: results not yet finalized");
        _;
    }

    /**
     * @dev Tally results for a constituency
     * @param constituencyId Constituency identifier
     * @param candidateIds Array of all candidate IDs in this constituency
     * @param expectedTotalVotes Expected total votes (for validation)
     */
    function tallyConstituency(
        uint256 constituencyId,
        uint256[] calldata candidateIds,
        uint256 expectedTotalVotes
    ) external onlyOwner {
        require(!resultsFinalized, "ResultsTallier: results already finalized");
        require(!constituencyTallied[constituencyId], "ResultsTallier: constituency already tallied");
        require(candidateIds.length > 0, "ResultsTallier: no candidates provided");

        // Ensure voting is closed
        (bool isOpen, , , ) = votingBooth.getVotingStatus();
        require(!isOpen, "ResultsTallier: voting must be closed before tallying");

        uint256 maxVotes = 0;
        uint256 winningCandidateId = 0;
        uint256 totalVotes = 0;
        bool hasTie = false;

        // First pass: find max votes and total
        for (uint256 i = 0; i < candidateIds.length; i++) {
            uint256 candidateId = candidateIds[i];
            uint256 voteCount = votingBooth.getVoteCount(candidateId);

            // Store candidate result
            candidateResults[candidateId] = CandidateResult({
                candidateId: candidateId,
                voteCount: voteCount,
                constituencyId: constituencyId
            });

            totalVotes += voteCount;

            if (voteCount > maxVotes) {
                maxVotes = voteCount;
                winningCandidateId = candidateId;
                hasTie = false;
            } else if (voteCount == maxVotes && maxVotes > 0) {
                hasTie = true;
            }
        }

        // Validate total votes if expected count provided
        if (expectedTotalVotes > 0) {
            require(
                totalVotes == expectedTotalVotes,
                "ResultsTallier: vote count mismatch"
            );
        }

        // Second pass: confirm tie (check if multiple candidates have max votes)
        if (hasTie) {
            uint256 tieCount = 0;
            for (uint256 i = 0; i < candidateIds.length; i++) {
                uint256 candidateId = candidateIds[i];
                uint256 voteCount = votingBooth.getVoteCount(candidateId);
                if (voteCount == maxVotes) {
                    tieCount++;
                }
            }

            if (tieCount > 1) {
                // Confirmed tie
                winningCandidateId = 0; // No winner in case of tie
                emit TieDetected(constituencyId, maxVotes);
            } else {
                hasTie = false;
            }
        }

        // Store constituency result
        constituencyResults[constituencyId] = ConstituencyResult({
            constituencyId: constituencyId,
            winnerCandidateId: winningCandidateId,
            winnerVoteCount: maxVotes,
            isTied: hasTie,
            totalVotes: totalVotes,
            isFinalized: true,
            finalizedAt: block.timestamp
        });

        constituencyTallied[constituencyId] = true;

        emit ConstituencyTallied(constituencyId, winningCandidateId, maxVotes, hasTie);

        if (!hasTie && winningCandidateId > 0) {
            emit WinnerDeclared(constituencyId, winningCandidateId, maxVotes);
        }
    }

    /**
     * @dev Finalize all results (makes them publicly viewable)
     */
    function finalizeResults() external onlyOwner {
        require(!resultsFinalized, "ResultsTallier: results already finalized");

        // Ensure voting is closed
        (bool isOpen, , , ) = votingBooth.getVotingStatus();
        require(!isOpen, "ResultsTallier: voting must be closed before finalization");

        resultsFinalized = true;
        finalizedAt = block.timestamp;

        emit ResultsFinalized(block.timestamp);
    }

    /**
     * @dev Get constituency result (only after finalization)
     * @param constituencyId Constituency identifier
     * @return result ConstituencyResult struct
     */
    function getConstituencyResult(uint256 constituencyId)
        external
        view
        onlyWhenFinalized
        returns (ConstituencyResult memory result)
    {
        require(
            constituencyTallied[constituencyId],
            "ResultsTallier: constituency not tallied"
        );
        return constituencyResults[constituencyId];
    }

    /**
     * @dev Get candidate result (only after finalization)
     * @param candidateId Candidate identifier
     * @return result CandidateResult struct
     */
    function getCandidateResult(uint256 candidateId)
        external
        view
        onlyWhenFinalized
        returns (CandidateResult memory result)
    {
        require(
            candidateResults[candidateId].candidateId > 0,
            "ResultsTallier: candidate not found"
        );
        return candidateResults[candidateId];
    }

    /**
     * @dev Check if a specific constituency has been tallied
     * @param constituencyId Constituency identifier
     * @return bool True if tallied
     */
    function isConstituencyTallied(uint256 constituencyId) external view returns (bool) {
        return constituencyTallied[constituencyId];
    }

    /**
     * @dev Get multiple constituency results at once (only after finalization)
     * @param constituencyIds Array of constituency identifiers
     * @return results Array of ConstituencyResult structs
     */
    function getBatchConstituencyResults(uint256[] calldata constituencyIds)
        external
        view
        onlyWhenFinalized
        returns (ConstituencyResult[] memory results)
    {
        results = new ConstituencyResult[](constituencyIds.length);

        for (uint256 i = 0; i < constituencyIds.length; i++) {
            require(
                constituencyTallied[constituencyIds[i]],
                "ResultsTallier: constituency not tallied"
            );
            results[i] = constituencyResults[constituencyIds[i]];
        }

        return results;
    }

    /**
     * @dev Get multiple candidate results at once (only after finalization)
     * @param candidateIds Array of candidate identifiers
     * @return results Array of CandidateResult structs
     */
    function getBatchCandidateResults(uint256[] calldata candidateIds)
        external
        view
        onlyWhenFinalized
        returns (CandidateResult[] memory results)
    {
        results = new CandidateResult[](candidateIds.length);

        for (uint256 i = 0; i < candidateIds.length; i++) {
            require(
                candidateResults[candidateIds[i]].candidateId > 0,
                "ResultsTallier: candidate not found"
            );
            results[i] = candidateResults[candidateIds[i]];
        }

        return results;
    }

    /**
     * @dev Get finalization status
     * @return isFinalized Whether results are finalized
     * @return timestamp When results were finalized
     */
    function getFinalizationStatus()
        external
        view
        returns (bool isFinalized, uint256 timestamp)
    {
        return (resultsFinalized, finalizedAt);
    }
}
