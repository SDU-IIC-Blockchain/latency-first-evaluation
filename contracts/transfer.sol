pragma solidity >=0.7.0 <0.9.0;
pragma abicoder v2;

contract TransferBalance {
    uint256 constant PerformanceFactor =1000;
    uint256 constant StateSizeFactor =10;

    struct __state_def_Transfer {
        uint64 Balance;
        bytes32[StateSizeFactor] Sig; // A time-consuming hash for simulating various gas costs
    }

    struct __tx_arg_Transfer {
        uint64 Value;
    }

    function __tx_do_Transfer(
        address[] memory addr,
        __state_def_Transfer[] memory states,
        __tx_arg_Transfer memory arg
    ) public pure returns (__state_def_Transfer[] memory newStates) {
        require(addr.length == states.length, "assert error");
        require(addr.length == 2, "the number of accounts must be 2");
        newStates = new __state_def_Transfer[](addr.length);
        require(states[0].Balance >= arg.Value, "insufficient funds");
        newStates[0].Balance = states[0].Balance - arg.Value;
        newStates[1].Balance = states[1].Balance + arg.Value;
        for (uint256 i = 0; i < 2; i++) {
            newStates[i].Sig[i % StateSizeFactor] = states[i].Sig[
                i % StateSizeFactor
            ];
            for (uint256 j = 0; j < PerformanceFactor; j++) {
                newStates[i].Sig[i % StateSizeFactor] = keccak256(
                    abi.encodePacked(
                        newStates[i].Sig[i % StateSizeFactor],
                        newStates[i].Balance
                    )
                );
            }
        }
        return newStates;
    }

    function __state_hash_Transfer(
        __state_def_Transfer memory state,
        __tx_arg_Transfer memory arg
    ) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(state.Balance, arg.Value));
    }

    function FundAccounts(address[] memory addr) public {
        for (uint256 i = 0; i < addr.length; i++) {
            __state_comp_dict_Transfer[addr[i]].Latest.Balance = 10000;
        }
    }

    function GetAccountBalance(address addr) public returns (uint64) {
        return __state_comp_dict_Transfer[addr].Latest.Balance;
    }

    mapping(address => __state_comp_element_Transfer)
        public __state_comp_dict_Transfer;
    struct __state_comp_element_Transfer {
        bytes32[] PendingStates;
        __state_def_Transfer Latest;
    }

    function __tx_online_Transfer(
        address[] memory addr,
        __tx_arg_Transfer memory arg
    ) public {
        __state_def_Transfer[]
            memory currentStates = new __state_def_Transfer[](addr.length);
        for (uint256 i = 0; i < addr.length; i++) {
            require(
                __state_comp_dict_Transfer[addr[i]].PendingStates.length == 0,
                "account has unfinished commitments"
            );
            currentStates[i] = (__state_comp_dict_Transfer[addr[i]].Latest);
        }
        __state_def_Transfer[] memory newStates = __tx_do_Transfer(
            addr,
            currentStates,
            arg
        );
        for (uint256 i = 0; i < addr.length; i++) {
            __state_comp_dict_Transfer[addr[i]].Latest = newStates[i];
        }
    }

    function __tx_proof_Transfer(
        address[] memory addr,
        __tx_arg_Transfer memory arg
    ) public {
        __state_def_Transfer[]
            memory currentStates = new __state_def_Transfer[](addr.length);
        for (uint i = 0; i < addr.length; i++) {
            require(
                __state_comp_dict_Transfer[addr[i]].PendingStates.length >= 1,
                "account does not have unfinished commitments"
            );
            currentStates[i] = (__state_comp_dict_Transfer[addr[i]].Latest);
        }
        __state_def_Transfer[] memory newStates = __tx_do_Transfer(
            addr,
            currentStates,
            arg
        );
        for (uint i = 0; i < addr.length; i++) {
            bytes32 stateHash = __state_hash_Transfer(newStates[i], arg);
            require(
                stateHash ==
                    __state_comp_dict_Transfer[addr[i]].PendingStates[0],
                "commitment mismatch"
            );
        }
        for (uint i = 0; i < addr.length; i++) {
            uint index = 0;
            for (
                uint j = index;
                j <
                __state_comp_dict_Transfer[addr[i]].PendingStates.length - 1;
                j++
            ) {
                __state_comp_dict_Transfer[addr[i]].PendingStates[
                        j
                    ] = __state_comp_dict_Transfer[addr[i]].PendingStates[
                    j + 1
                ];
            }
            __state_comp_dict_Transfer[addr[i]].PendingStates.pop();
            __state_comp_dict_Transfer[addr[i]].Latest = newStates[i];
        }
    }

    function __tx_offline_Transfer(
        address[] memory addr,
        __state_def_Transfer[] memory states,
        __tx_arg_Transfer memory arg
    )
        public
        pure
        returns (
            __state_def_Transfer[] memory newStates,
            bytes32[] memory newStateHashes
        )
    {
        newStates = __tx_do_Transfer(addr, states, arg);
        newStateHashes = new bytes32[](addr.length);
        for (uint i = 0; i < addr.length; i++) {
            newStateHashes[i] = __state_hash_Transfer(newStates[i], arg);
        }
        return (newStates, newStateHashes);
    }

    function __tx_commit_Transfer(address[] memory addr, bytes32[] memory hash)
        public
    {
        for (uint i = 0; i < addr.length; i++) {
            __state_comp_dict_Transfer[addr[i]].PendingStates.push(hash[i]);
        }
    }

    function __tx_pending_len_Transfer(address addr)
        public
        view
        returns (uint)
    {
        return __state_comp_dict_Transfer[addr].PendingStates.length;
    }

    function __tx_state_latest_Transfer(address addr)
        public
        view
        returns (__state_def_Transfer memory)
    {
        return __state_comp_dict_Transfer[addr].Latest;
    }
}
