const fs = require('fs');
const path = require('path');
const VoterRegistry = artifacts.require("VoterRegistry");
const VotingBooth = artifacts.require("VotingBooth");
const ResultsTallier = artifacts.require("ResultsTallier");
const ElectionController = artifacts.require("ElectionController");

module.exports = async function(deployer, network, accounts) {
  console.log("Deploying ElectionController...");
  console.log("Network:", network);
  console.log("Deployer account:", accounts[0]);

  // Get deployed contracts
  const registry = await VoterRegistry.deployed();
  const booth = await VotingBooth.deployed();
  const tallier = await ResultsTallier.deployed();

  console.log("Using VoterRegistry at:", registry.address);
  console.log("Using VotingBooth at:", booth.address);
  console.log("Using ResultsTallier at:", tallier.address);

  // Election details
  const electionId = 1;
  const electionName = "General Election 2026";

  await deployer.deploy(
    ElectionController,
    electionId,
    electionName,
    registry.address,
    booth.address,
    tallier.address
  );

  const controller = await ElectionController.deployed();

  console.log("✓ ElectionController deployed at:", controller.address);
  console.log("  Owner:", await controller.owner());
  console.log("  Election ID:", (await controller.electionId()).toString());
  console.log("  Election Name:", await controller.electionName());
  console.log("  Current Phase:", await controller.getCurrentPhase());

  // Update VoterRegistry to authorize ElectionController
  console.log("\nUpdating VoterRegistry authorization...");
  const tx = await registry.setElectionController(controller.address);
  console.log("✓ VoterRegistry authorized ElectionController");
  console.log("  Transaction hash:", tx.tx);

  // Verify authorization
  const authorizedController = await registry.electionController();
  console.log("  Verified controller address:", authorizedController);

  // Write deployed addresses to JSON file
  const addresses = {
    network: network,
    networkId: await web3.eth.net.getId(),
    deployer: accounts[0],
    deployedAt: new Date().toISOString(),
    contracts: {
      VoterRegistry: {
        address: registry.address,
        owner: await registry.owner()
      },
      VotingBooth: {
        address: booth.address,
        owner: await booth.owner(),
        electionId: (await booth.electionId()).toString()
      },
      ResultsTallier: {
        address: tallier.address,
        owner: await tallier.owner()
      },
      ElectionController: {
        address: controller.address,
        owner: await controller.owner(),
        electionId: (await controller.electionId()).toString(),
        electionName: await controller.electionName()
      }
    }
  };

  const outputPath = path.join(__dirname, '..', '..', 'deployed_addresses.json');
  fs.writeFileSync(outputPath, JSON.stringify(addresses, null, 2));

  console.log("\n✓ Deployment complete!");
  console.log("✓ Contract addresses saved to:", outputPath);
  console.log("\n=== Summary ===");
  console.log("VoterRegistry:       ", registry.address);
  console.log("VotingBooth:         ", booth.address);
  console.log("ResultsTallier:      ", tallier.address);
  console.log("ElectionController:  ", controller.address);
  console.log("==============\n");
};
