require('dotenv').config();
const HDWalletProvider = require('@truffle/hdwallet-provider');

module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "1337",
      gas: 6721975,
      gasPrice: 20000000000
    },
    test: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "1337",
      gas: 6721975,
      gasPrice: 20000000000
    },
    // Sepolia testnet (Ethereum)
    sepolia: {
      provider: () => new HDWalletProvider(
        process.env.DEPLOYER_PRIVATE_KEY,
        `https://sepolia.infura.io/v3/${process.env.INFURA_API_KEY}`
      ),
      network_id: 11155111,       // Sepolia's network id
      gas: 5500000,               // Gas limit
      gasPrice: 10000000000,      // 10 gwei
      confirmations: 2,           // # of confirmations to wait
      timeoutBlocks: 200,         // # of blocks before deployment times out
      skipDryRun: true            // Skip dry run before migrations
    }
  },

  contracts_directory: './contracts',
  contracts_build_directory: './build/contracts',

  compilers: {
    solc: {
      version: "0.8.20",
      settings: {
        optimizer: {
          enabled: true,
          runs: 200
        },
        evmVersion: "paris"
      }
    }
  },

  mocha: {
    timeout: 100000,
    useColors: true
  },

  plugins: []
};
