const VotingBooth = artifacts.require("VotingBooth");
const ResultsTallier = artifacts.require("ResultsTallier");

module.exports = async function(deployer, network, accounts) {
  console.log("Deploying ResultsTallier...");
  console.log("Network:", network);
  console.log("Deployer account:", accounts[0]);

  // Get deployed VotingBooth
  const booth = await VotingBooth.deployed();
  console.log("Using VotingBooth at:", booth.address);

  await deployer.deploy(ResultsTallier, booth.address);
  const tallier = await ResultsTallier.deployed();

  console.log("✓ ResultsTallier deployed at:", tallier.address);
  console.log("  Owner:", await tallier.owner());
  console.log("  Voting Booth:", await tallier.votingBooth());
  console.log("  Results finalized:", await tallier.resultsFinalized());
};
