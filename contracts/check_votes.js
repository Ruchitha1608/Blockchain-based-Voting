const Web3 = require('web3');
const fs = require('fs');

const web3 = new Web3('http://127.0.0.1:8545');

async function checkVotes() {
    try {
        // Load contract artifacts
        const ElectionController = JSON.parse(fs.readFileSync('build/contracts/ElectionController.json'));
        const VotingBooth = JSON.parse(fs.readFileSync('build/contracts/VotingBooth.json'));
        const ResultsTallier = JSON.parse(fs.readFileSync('build/contracts/ResultsTallier.json'));
        
        // Get deployed addresses
        const networkId = '1337';
        const controllerAddress = ElectionController.networks[networkId].address;
        const boothAddress = VotingBooth.networks[networkId].address;
        const tallierAddress = ResultsTallier.networks[networkId].address;
        
        console.log('Contract Addresses:');
        console.log('ElectionController:', controllerAddress);
        console.log('VotingBooth:', boothAddress);
        console.log('ResultsTallier:', tallierAddress);
        console.log('');
        
        // Create contract instances
        const controller = new web3.eth.Contract(ElectionController.abi, controllerAddress);
        const booth = new web3.eth.Contract(VotingBooth.abi, boothAddress);
        const tallier = new web3.eth.Contract(ResultsTallier.abi, tallierAddress);
        
        // Check if election is started
        const isActive = await controller.methods.isElectionActive().call();
        console.log('Election Active:', isActive);
        
        // Check voting status (try candidate ID 0)
        try {
            const candidateVotes = await booth.methods.getCandidateVoteCount(0).call();
            console.log('Candidate 0 votes (from VotingBooth):', candidateVotes);
        } catch (e) {
            console.log('Error getting votes from VotingBooth:', e.message);
        }
        
        // Check if results are finalized
        try {
            const result = await tallier.methods.getCandidateResult(0).call();
            console.log('Candidate 0 result (from ResultsTallier):', result);
        } catch (e) {
            console.log('Error getting result from ResultsTallier:', e.message);
        }
        
        // Get past VoteCast events
        console.log('\nSearching for VoteCast events...');
        const events = await booth.getPastEvents('VoteCast', {
            fromBlock: 0,
            toBlock: 'latest'
        });
        console.log('Total VoteCast events:', events.length);
        events.forEach((event, idx) => {
            console.log(`Event ${idx + 1}:`, event.returnValues);
        });
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

checkVotes();
