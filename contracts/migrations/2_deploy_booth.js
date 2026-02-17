const VoterRegistry = artifacts.require("VoterRegistry");
const VotingBooth = artifacts.require("VotingBooth");

module.exports = async function(deployer, network, accounts) {
  console.log("Deploying VotingBooth...");
  console.log("Network:", network);
  console.log("Deployer account:", accounts[0]);

  // Get deployed VoterRegistry
  const registry = await VoterRegistry.deployed();
  console.log("Using VoterRegistry at:", registry.address);

  // Election ID for this deployment
  const electionId = 1;

  await deployer.deploy(VotingBooth, registry.address, electionId);
  const booth = await VotingBooth.deployed();

  console.log("✓ VotingBooth deployed at:", booth.address);
  console.log("  Owner:", await booth.owner());
  console.log("  Election ID:", (await booth.electionId()).toString());
  console.log("  Voter Registry:", await booth.voterRegistry());
  console.log("  Voting open:", await booth.votingOpen());
};
