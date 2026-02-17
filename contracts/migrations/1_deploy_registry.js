const VoterRegistry = artifacts.require("VoterRegistry");

module.exports = async function(deployer, network, accounts) {
  console.log("Deploying VoterRegistry...");
  console.log("Network:", network);
  console.log("Deployer account:", accounts[0]);

  // Deploy with placeholder controller address (will be updated after ElectionController deploys)
  const placeholderController = "0x0000000000000000000000000000000000000001";

  await deployer.deploy(VoterRegistry, placeholderController);
  const registry = await VoterRegistry.deployed();

  console.log("✓ VoterRegistry deployed at:", registry.address);
  console.log("  Owner:", await registry.owner());
  console.log("  Registration open:", await registry.registrationOpen());
};
