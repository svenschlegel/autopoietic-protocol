// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "src/SoulboundMass.sol";
import "src/EscrowCore.sol";
import "src/AutoToken.sol";
import "src/Treasury.sol";

/**
 * @title DeployAutopoietic
 * @notice Deploys the full Autopoietic Protocol to Base Sepolia
 * @dev Run with:
 *   forge script script/Deploy.s.sol:DeployAutopoietic \
 *     --rpc-url $BASE_SEPOLIA_RPC_URL \
 *     --private-key $DEPLOYER_PRIVATE_KEY \
 *     --broadcast \
 *     --verify
 */
contract DeployAutopoietic is Script {

    // Base Sepolia USDC (Circle's official testnet USDC)
    address constant USDC = 0x036CbD53842c5426634e7929541eC2318f3dCF7e;

    // Minimum treasury reserve: 1,000 USDC for testnet (6 decimals)
    uint256 constant MIN_RESERVE = 1_000_000_000; // 1,000 USDC

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        // For testnet: deployer acts as both architect and core contributor
        address architect = deployer;
        address coreContributor = deployer;

        console.log("========================================");
        console.log("  AUTOPOIETIC PROTOCOL DEPLOYMENT");
        console.log("  Network: Base Sepolia");
        console.log("  Deployer:", deployer);
        console.log("========================================");

        vm.startBroadcast(deployerPrivateKey);

        // ── Step 1: Deploy SoulboundMass ────────────────────
        SoulboundMass soulboundMass = new SoulboundMass();
        console.log("1. SoulboundMass:", address(soulboundMass));

        // ── Step 2: Deploy Treasury ─────────────────────────
        Treasury treasury = new Treasury(USDC, MIN_RESERVE);
        console.log("2. Treasury:     ", address(treasury));

        // ── Step 3: Deploy EscrowCore ───────────────────────
        EscrowCore escrowCore = new EscrowCore(
            USDC,
            address(soulboundMass),
            address(treasury),
            coreContributor
        );
        console.log("3. EscrowCore:   ", address(escrowCore));

        // ── Step 4: Deploy AutoToken ────────────────────────
        AutoToken autoToken = new AutoToken(architect, address(treasury));
        console.log("4. AutoToken:    ", address(autoToken));

        // ── Step 5: Wire cross-references ───────────────────
        soulboundMass.authorizeMinter(address(escrowCore));
        autoToken.setEscrowCore(address(escrowCore));
        treasury.setEscrowCore(address(escrowCore));
        console.log("5. Cross-references wired");

        vm.stopBroadcast();

        // ── Output deployment addresses ─────────────────────
        console.log("");
        console.log("========================================");
        console.log("  DEPLOYMENT COMPLETE");
        console.log("========================================");
        console.log("USDC:          ", USDC);
        console.log("SoulboundMass: ", address(soulboundMass));
        console.log("Treasury:      ", address(treasury));
        console.log("EscrowCore:    ", address(escrowCore));
        console.log("AutoToken:     ", address(autoToken));
        console.log("Architect:     ", architect);
        console.log("========================================");
        console.log("");
        console.log("Save these addresses in your .env file!");

        // Write addresses to a JSON file for the Node Client
        string memory json = string(abi.encodePacked(
            '{"network":"base_sepolia",',
            '"usdc":"', vm.toString(USDC), '",',
            '"soulbound_mass":"', vm.toString(address(soulboundMass)), '",',
            '"treasury":"', vm.toString(address(treasury)), '",',
            '"escrow_core":"', vm.toString(address(escrowCore)), '",',
            '"auto_token":"', vm.toString(address(autoToken)), '",',
            '"architect":"', vm.toString(architect), '"}'
        ));
    }
}
