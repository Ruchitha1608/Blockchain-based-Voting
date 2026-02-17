import { ethers } from 'ethers';

// Create provider from blockchain URL
const getProvider = () => {
  const blockchainUrl = process.env.REACT_APP_BLOCKCHAIN_URL || 'http://localhost:8545';
  return new ethers.JsonRpcProvider(blockchainUrl);
};

let provider;

try {
  provider = getProvider();
} catch (error) {
  console.error('Failed to initialize Web3 provider:', error);
  provider = null;
}

/**
 * Get the current block number
 * @returns {Promise<number>} The current block number
 */
export const getBlockNumber = async () => {
  try {
    if (!provider) {
      throw new Error('Web3 provider not initialized');
    }
    const blockNumber = await provider.getBlockNumber();
    return blockNumber;
  } catch (error) {
    console.error('Error getting block number:', error);
    throw error;
  }
};

/**
 * Get transaction details by hash
 * @param {string} txHash - Transaction hash
 * @returns {Promise<object>} Transaction details
 */
export const getTransaction = async (txHash) => {
  try {
    if (!provider) {
      throw new Error('Web3 provider not initialized');
    }
    if (!txHash || typeof txHash !== 'string') {
      throw new Error('Invalid transaction hash');
    }
    const transaction = await provider.getTransaction(txHash);
    if (!transaction) {
      throw new Error('Transaction not found');
    }
    return transaction;
  } catch (error) {
    console.error('Error getting transaction:', error);
    throw error;
  }
};

/**
 * Get transaction receipt by hash
 * @param {string} txHash - Transaction hash
 * @returns {Promise<object>} Transaction receipt
 */
export const getTransactionReceipt = async (txHash) => {
  try {
    if (!provider) {
      throw new Error('Web3 provider not initialized');
    }
    if (!txHash || typeof txHash !== 'string') {
      throw new Error('Invalid transaction hash');
    }
    const receipt = await provider.getTransactionReceipt(txHash);
    if (!receipt) {
      throw new Error('Transaction receipt not found');
    }
    return receipt;
  } catch (error) {
    console.error('Error getting transaction receipt:', error);
    throw error;
  }
};

/**
 * Format an Ethereum address for display
 * @param {string} address - Ethereum address
 * @param {number} startChars - Number of characters to show at start (default: 6)
 * @param {number} endChars - Number of characters to show at end (default: 4)
 * @returns {string} Formatted address (e.g., "0x1234...5678")
 */
export const formatAddress = (address, startChars = 6, endChars = 4) => {
  try {
    if (!address || typeof address !== 'string') {
      throw new Error('Invalid address');
    }

    // Validate Ethereum address format
    if (!ethers.isAddress(address)) {
      throw new Error('Invalid Ethereum address format');
    }

    // If address is too short, return as is
    if (address.length <= startChars + endChars) {
      return address;
    }

    return `${address.substring(0, startChars)}...${address.substring(address.length - endChars)}`;
  } catch (error) {
    console.error('Error formatting address:', error);
    return address;
  }
};

/**
 * Wait for a transaction to be mined
 * @param {string} txHash - Transaction hash
 * @param {number} confirmations - Number of confirmations to wait for (default: 1)
 * @returns {Promise<object>} Transaction receipt
 */
export const waitForTransaction = async (txHash, confirmations = 1) => {
  try {
    if (!provider) {
      throw new Error('Web3 provider not initialized');
    }
    if (!txHash || typeof txHash !== 'string') {
      throw new Error('Invalid transaction hash');
    }

    const receipt = await provider.waitForTransaction(txHash, confirmations);
    if (!receipt) {
      throw new Error('Transaction failed or was not mined');
    }
    return receipt;
  } catch (error) {
    console.error('Error waiting for transaction:', error);
    throw error;
  }
};

/**
 * Get gas price
 * @returns {Promise<bigint>} Current gas price
 */
export const getGasPrice = async () => {
  try {
    if (!provider) {
      throw new Error('Web3 provider not initialized');
    }
    const feeData = await provider.getFeeData();
    return feeData.gasPrice;
  } catch (error) {
    console.error('Error getting gas price:', error);
    throw error;
  }
};

/**
 * Get network information
 * @returns {Promise<object>} Network details
 */
export const getNetwork = async () => {
  try {
    if (!provider) {
      throw new Error('Web3 provider not initialized');
    }
    const network = await provider.getNetwork();
    return {
      chainId: Number(network.chainId),
      name: network.name,
    };
  } catch (error) {
    console.error('Error getting network:', error);
    throw error;
  }
};

/**
 * Check if provider is connected
 * @returns {boolean} Connection status
 */
export const isConnected = () => {
  return provider !== null;
};

/**
 * Reinitialize provider (useful for reconnection)
 * @returns {object} New provider instance
 */
export const reinitializeProvider = () => {
  try {
    provider = getProvider();
    return provider;
  } catch (error) {
    console.error('Failed to reinitialize provider:', error);
    throw error;
  }
};

export default {
  getBlockNumber,
  getTransaction,
  getTransactionReceipt,
  formatAddress,
  waitForTransaction,
  getGasPrice,
  getNetwork,
  isConnected,
  reinitializeProvider,
};
