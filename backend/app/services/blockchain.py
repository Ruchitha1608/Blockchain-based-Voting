"""
Blockchain service for interacting with smart contracts
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from web3 import Web3
from web3.contract import Contract
from eth_account import Account
import structlog

from app.config import settings

logger = structlog.get_logger()


class BlockchainError(Exception):
    """Custom exception for blockchain operations"""
    pass


class BlockchainService:
    """
    Service for interacting with election smart contracts on blockchain
    """

    def __init__(self):
        self.web3 = None
        self.voter_registry = None
        self.voting_booth = None
        self.results_tallier = None
        self.election_controller = None
        self.default_account = None
        self.connected = False
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize Web3 connection and load contracts"""
        try:
            # Connect to Ganache
            self.web3 = Web3(Web3.HTTPProvider(settings.GANACHE_URL))

            if not self.web3.is_connected():
                logger.warning("blockchain_not_connected", url=settings.GANACHE_URL,
                             message="Blockchain node not available. Blockchain features will be disabled.")
                return

            self.connected = True
            logger.info("blockchain_connected", url=settings.GANACHE_URL)

            # Set default account (first Ganache account)
            accounts = self.web3.eth.accounts
            if accounts:
                self.default_account = accounts[0]
                logger.info("default_account_set", account=self.default_account)

            # Load contracts if deployed
            self._load_contracts()

        except Exception as e:
            logger.warning("blockchain_initialization_failed", error=str(e),
                         message="Blockchain features will be disabled. Start Ganache to enable.")

    def _ensure_connected(self):
        """Raise error if blockchain is not connected"""
        if not self.connected:
            raise BlockchainError("Blockchain node not connected. Please start Ganache at " + settings.GANACHE_URL)

    def _load_contracts(self):
        """Load deployed contract instances from build artifacts"""
        try:
            # Path to contract build directory
            build_path = Path(__file__).parent.parent.parent / "contracts" / "build" / "contracts"

            if not build_path.exists():
                logger.warning("contracts_not_deployed", path=str(build_path))
                return

            # Load each contract
            self.voter_registry = self._load_contract("VoterRegistry", build_path)
            self.voting_booth = self._load_contract("VotingBooth", build_path)
            self.results_tallier = self._load_contract("ResultsTallier", build_path)
            self.election_controller = self._load_contract("ElectionController", build_path)

            logger.info("contracts_loaded", contracts=["VoterRegistry", "VotingBooth", "ResultsTallier", "ElectionController"])

        except Exception as e:
            logger.warning("contract_loading_failed", error=str(e))

    def _load_contract(self, contract_name: str, build_path: Path) -> Contract:
        """Load a single contract from build artifacts"""
        try:
            artifact_path = build_path / f"{contract_name}.json"

            if not artifact_path.exists():
                logger.warning("contract_artifact_not_found", contract=contract_name)
                return None

            with open(artifact_path, 'r') as f:
                artifact = json.load(f)

            # Get contract address from networks
            network_id = str(settings.GANACHE_NETWORK_ID)
            if 'networks' not in artifact or network_id not in artifact['networks']:
                logger.warning("contract_not_deployed", contract=contract_name, network_id=network_id)
                return None

            address = artifact['networks'][network_id]['address']
            abi = artifact['abi']

            # Create contract instance
            contract = self.web3.eth.contract(address=address, abi=abi)

            logger.debug("contract_loaded", contract=contract_name, address=address)
            return contract

        except Exception as e:
            logger.error("contract_load_failed", contract=contract_name, error=str(e))
            return None

    def register_voter_on_chain(self, voter_hash: str, constituency_on_chain_id: int) -> str:
        """
        Register a voter on the blockchain

        Args:
            voter_hash: Keccak256 hash of voter identity (0x prefixed)
            constituency_on_chain_id: Constituency ID on blockchain

        Returns:
            str: Transaction hash
        """
        try:
            if not self.election_controller:
                raise BlockchainError("Election controller not loaded")

            # Convert hex string to bytes32
            voter_hash_bytes = Web3.to_bytes(hexstr=voter_hash)

            # Call registerVoter function
            tx_hash = self.election_controller.functions.registerVoter(
                voter_hash_bytes,
                constituency_on_chain_id
            ).transact({'from': self.default_account})

            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] != 1:
                raise BlockchainError("Voter registration transaction failed")

            logger.info("voter_registered_on_chain", tx_hash=tx_hash.hex(), voter_hash=voter_hash)
            return tx_hash.hex()

        except Exception as e:
            logger.error("voter_registration_failed", error=str(e))
            raise BlockchainError(f"Failed to register voter: {str(e)}")

    def submit_vote_on_chain(
        self,
        voter_hash: str,
        candidate_on_chain_id: int,
        constituency_on_chain_id: int
    ) -> Dict[str, Any]:
        """
        Submit a vote to the blockchain

        Args:
            voter_hash: Keccak256 hash of voter identity
            candidate_on_chain_id: Candidate ID on blockchain
            constituency_on_chain_id: Constituency ID on blockchain

        Returns:
            dict: {tx_hash, block_number, gas_used}
        """
        try:
            if not self.election_controller:
                raise BlockchainError("Election controller not loaded")

            # Convert hex string to bytes32
            voter_hash_bytes = Web3.to_bytes(hexstr=voter_hash)

            # Call submitVote function
            tx_hash = self.election_controller.functions.submitVote(
                voter_hash_bytes,
                candidate_on_chain_id,
                constituency_on_chain_id
            ).transact({'from': self.default_account})

            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] != 1:
                raise BlockchainError("Vote submission transaction failed")

            result = {
                'tx_hash': tx_hash.hex(),
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed']
            }

            logger.info("vote_submitted_on_chain", **result)
            return result

        except Exception as e:
            logger.error("vote_submission_failed", error=str(e))
            raise BlockchainError(f"Failed to submit vote: {str(e)}")

    def is_voter_eligible(self, voter_hash: str) -> bool:
        """
        Check if a voter is eligible to vote

        Args:
            voter_hash: Keccak256 hash of voter identity

        Returns:
            bool: True if eligible, False otherwise
        """
        try:
            if not self.voter_registry:
                raise BlockchainError("Voter registry not loaded")

            voter_hash_bytes = Web3.to_bytes(hexstr=voter_hash)

            eligible = self.voter_registry.functions.isEligible(voter_hash_bytes).call()

            logger.debug("voter_eligibility_checked", voter_hash=voter_hash, eligible=eligible)
            return eligible

        except Exception as e:
            logger.error("eligibility_check_failed", error=str(e))
            return False

    def get_election_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive election summary from blockchain

        Returns:
            dict: Election summary with all statistics
        """
        try:
            if not self.election_controller:
                raise BlockchainError("Election controller not loaded")

            summary = self.election_controller.functions.getElectionSummary().call()

            result = {
                'election_id': summary[0],
                'election_name': summary[1],
                'phase': summary[2],
                'total_registered': summary[3],
                'total_voted': summary[4],
                'turnout_basis_points': summary[5],
                'voting_is_open': summary[6],
                'results_are_finalized': summary[7]
            }

            logger.info("election_summary_retrieved", **result)
            return result

        except Exception as e:
            logger.error("election_summary_failed", error=str(e))
            raise BlockchainError(f"Failed to get election summary: {str(e)}")

    def get_candidate_vote_count(self, candidate_on_chain_id: int) -> int:
        """
        Get vote count for a candidate (only after election finalized)

        Args:
            candidate_on_chain_id: Candidate ID on blockchain

        Returns:
            int: Number of votes
        """
        try:
            if not self.results_tallier:
                raise BlockchainError("Results tallier not loaded")

            # Get candidate result
            result = self.results_tallier.functions.getCandidateResult(candidate_on_chain_id).call()

            vote_count = result[1]  # result = (candidateId, voteCount, constituencyId)

            logger.info("candidate_vote_count_retrieved", candidate_id=candidate_on_chain_id, votes=vote_count)
            return vote_count

        except Exception as e:
            logger.error("vote_count_retrieval_failed", error=str(e))
            raise BlockchainError(f"Failed to get vote count: {str(e)}")

    def finalize_election(
        self,
        constituency_ids: List[int],
        candidate_ids_per_constituency: List[List[int]],
        expected_votes_per_constituency: List[int]
    ) -> str:
        """
        Tally and finalize election results

        Args:
            constituency_ids: List of all constituency IDs
            candidate_ids_per_constituency: 2D list of candidate IDs for each constituency
            expected_votes_per_constituency: Expected vote counts for validation

        Returns:
            str: Transaction hash
        """
        try:
            if not self.election_controller:
                raise BlockchainError("Election controller not loaded")

            # Call tallyAndFinalize function
            tx_hash = self.election_controller.functions.tallyAndFinalize(
                constituency_ids,
                candidate_ids_per_constituency,
                expected_votes_per_constituency
            ).transact({'from': self.default_account, 'gas': 5000000})

            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] != 1:
                raise BlockchainError("Election finalization transaction failed")

            logger.info("election_finalized", tx_hash=tx_hash.hex())
            return tx_hash.hex()

        except Exception as e:
            logger.error("election_finalization_failed", error=str(e))
            raise BlockchainError(f"Failed to finalize election: {str(e)}")

    def get_constituency_result(self, constituency_on_chain_id: int) -> Dict[str, Any]:
        """
        Get results for a specific constituency

        Args:
            constituency_on_chain_id: Constituency ID on blockchain

        Returns:
            dict: Constituency result
        """
        try:
            if not self.results_tallier:
                raise BlockchainError("Results tallier not loaded")

            result = self.results_tallier.functions.getConstituencyResult(constituency_on_chain_id).call()

            constituency_result = {
                'constituency_id': result[0],
                'winner_candidate_id': result[1],
                'winner_vote_count': result[2],
                'is_tied': result[3],
                'total_votes': result[4],
                'is_finalized': result[5],
                'finalized_at': result[6]
            }

            logger.info("constituency_result_retrieved", constituency_id=constituency_on_chain_id)
            return constituency_result

        except Exception as e:
            logger.error("constituency_result_failed", error=str(e))
            raise BlockchainError(f"Failed to get constituency result: {str(e)}")

    def start_election(self, start_time: int, end_time: int) -> str:
        """
        Start the election

        Args:
            start_time: Unix timestamp for voting start
            end_time: Unix timestamp for voting end

        Returns:
            str: Transaction hash
        """
        try:
            if not self.election_controller:
                raise BlockchainError("Election controller not loaded")

            tx_hash = self.election_controller.functions.startElection(
                start_time,
                end_time
            ).transact({'from': self.default_account})

            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] != 1:
                raise BlockchainError("Start election transaction failed")

            logger.info("election_started", tx_hash=tx_hash.hex())
            return tx_hash.hex()

        except Exception as e:
            logger.error("start_election_failed", error=str(e))
            raise BlockchainError(f"Failed to start election: {str(e)}")

    def close_election(self) -> str:
        """
        Close the election

        Returns:
            str: Transaction hash
        """
        try:
            if not self.election_controller:
                raise BlockchainError("Election controller not loaded")

            tx_hash = self.election_controller.functions.closeElection().transact({'from': self.default_account})

            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] != 1:
                raise BlockchainError("Close election transaction failed")

            logger.info("election_closed", tx_hash=tx_hash.hex())
            return tx_hash.hex()

        except Exception as e:
            logger.error("close_election_failed", error=str(e))
            raise BlockchainError(f"Failed to close election: {str(e)}")

    def register_candidate(self, candidate_id: int, constituency_id: int) -> str:
        """
        Register a candidate on blockchain

        Args:
            candidate_id: Candidate identifier
            constituency_id: Constituency identifier

        Returns:
            str: Transaction hash
        """
        try:
            if not self.election_controller:
                raise BlockchainError("Election controller not loaded")

            tx_hash = self.election_controller.functions.registerCandidate(
                candidate_id,
                constituency_id
            ).transact({'from': self.default_account})

            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] != 1:
                raise BlockchainError("Candidate registration transaction failed")

            logger.info("candidate_registered", tx_hash=tx_hash.hex(), candidate_id=candidate_id)
            return tx_hash.hex()

        except Exception as e:
            logger.error("candidate_registration_failed", error=str(e))
            raise BlockchainError(f"Failed to register candidate: {str(e)}")


# Global blockchain service instance
blockchain_service = BlockchainService()
