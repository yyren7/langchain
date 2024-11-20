// ツールボックスの定義 
const toolbox = {
    "contents": [
        {
            // オリジナル
            "kind": "CATEGORY",
            "name": "Robot",
            "colour": 10,
            "contents": [
                {
                    "kind": "BLOCK",
                    "type": "select_robot"
                },
                {
                   "kind": "BLOCK",
                   "type": "moveL"
                },
                {
                    "kind": "BLOCK",
                    "type": "set_motor"
                },
                {
                    "kind": "BLOCK",
                    "type": "origin"
                },
            ]
        },
        // {
        //     "kind": "CATEGORY",
        //     "name": "Basic",
        //     "colour": 60,
        //     "contents": [
        //         {
        //             "kind": "BLOCK",
        //             "type": "return"
        //         },
        //     ]
        // },
        {
            "kind": "CATEGORY",
            "name": "Logic",
            "colour": 200,
            "contents": [
                {
                    "kind": "BLOCK",
                    "type": "controls_if"
                },
                {
                    "kind": "BLOCK",
                    "type": "loop"
                },
                {
                    "kind": "BLOCK",
                    "type": "return"
                },
                {
                    "kind": "BLOCK",
                    "type": "wait_during"
                },
            ]
        },
        {
            "kind": "CATEGORY",
            "name": "Pallet",
            "colour": 260,
            "contents": 
            [
                {
                    "kind": "BLOCK",
                    "type": "set_pallet"
                },
                {
                    "kind": "BLOCK",
                    "type": "move_next_pallet"
                },
                {
                    "kind": "BLOCK",
                    "type": "reset_pallet"
                },
            ]
        },
        {
            "kind": "CATEGORY",
            "name": "Condition",
            "colour": 60,
            "contents": [
                {
                    "kind": "BLOCK",
                    "type": "check_pallet"
                },
            ]
        },
        {
            "kind": "CATEGORY",
            "name": "IO",
            "colour": 120,
            "contents": [
                {
                    "kind": "BLOCK",
                    "type": "set_output_during"
                },
                {
                    "kind": "BLOCK",
                    "type": "set_output_wait"
                },
                {
                    "kind": "BLOCK",
                    "type": "wait_input"
                },
            ]
        },
        {
            "kind": "CATEGORY",
            "name": "Hand",
            "colour": 160,
            "contents": [
                {
                    "kind": "BLOCK",
                    "type": "hand_pick"
                },
                {
                    "kind": "BLOCK",
                    "type": "hand_place"
                },
            ]
        },
        {
            "kind": "CATEGORY",
            "name": "Parallel",
            "colour": 315,
            "contents": [
                {
                    "kind": "BLOCK",
                    "type": "start_thred"
                },
                {
                    "kind": "BLOCK",
                    "type": "set_flag"
                },
                {
                    "kind": "BLOCK",
                    "type": "wait_end"
                },

            ]
        },
        // {
        //     "kind": "CATEGORY",
        //     "name": "Variables",
        //     "colour": 10,
        //     "contents": [
        //         {
        //             "kind": "BLOCK",
        //             "type": "variables_get"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "variables_set"
        //         },
        //     ]
        // },

        // {
        //     "kind": "CATEGORY",
        //     "name": "Functions",
        //     "colour": 10,
        //     "contents": [
        //         {
        //             "kind": "BLOCK",
        //             "type": "procedures_defnoreturn"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "procedures_defreturn"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "procedures_ifreturn"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "procedures_callnoreturn"
        //          },
        //          {
        //              "kind": "BLOCK",
        //              "type": "procedures_callreturn"
        //          },
        //     ]
        // },

        // // デフォルト
        // {
        // "kind": "CATEGORY",
        // "name": "Logic",
        // "colour": 10,
        // "contents": [
        //     {
        //         "kind": "BLOCK",
        //         "type": "controls_if"
        //     },
        //     {
        //         "kind": "BLOCK",
        //         "type": "logic_compare"
        //     },
        //     {
        //         "kind": "BLOCK",
        //         "type": "logic_operation"
        //     },
        //     {
        //         "kind": "BLOCK",
        //         "type": "logic_negate"
        //     },
        //     {
        //         "kind": "BLOCK",
        //         "type": "logic_boolean"
        //     },
        //     {
        //         "kind": "BLOCK",
        //         "type": "logic_null"
        //     },
        //     {
        //         "kind": "BLOCK",
        //         "type": "logic_ternary"
        //     },
        // ]
        // },
        // {
        // "kind": "CATEGORY",
        // "name": "Loop",
        // "colour": 40,
        // "contents": [
        //     {
        //         "kind": "BLOCK",
        //         "type": "controls_repeat_ext"
        //     },
        //     {
        //         "kind": "BLOCK",
        //         "type": "controls_whileUntil"
        //     },
        //     {
        //         "kind": "BLOCK",
        //         "type": "controls_for"
        //     },
        //     {
        //         "kind": "BLOCK",
        //         "type": "controls_forEach"
        //     },
        //     {
        //         "kind": "BLOCK",
        //         "type": "controls_flow_statements"
        //     },
        // ]
        // },
        // {
        //     "kind": "CATEGORY",
        //     "name": "Math",
        //     "colour": 70,
        //     "contents": [
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_number"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_arithmetic"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_single"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_trig"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_constant"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_number_property"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_on_list"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_modulo"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_round"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_constrain"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_random_int"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_random_float"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "math_atan2"
        //         },
        //     ]
        // },
        // {
        //     "kind": "CATEGORY",
        //     "name": "Text",
        //     "colour": 100,
        //     "contents": [
        //         {
        //             "kind": "BLOCK",
        //             "type": "text"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "text_join"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "text_append"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "text_length"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "text_isEmpty"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "text_indexOf"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "text_charAt"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "text_getSubstring"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "text_changeCase"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "text_trim"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "text_print"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "text_prompt_ext"
        //         },
        //     ]
        // },
        // {
        //     "kind": "CATEGORY",
        //     "name": "List",
        //     "colour": 140,
        //     "contents": [
        //         {
        //             "kind": "BLOCK",
        //             "type": "lists_create_with"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "lists_repeat"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "lists_length"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "lists_isEmpty"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "lists_indexOf"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "lists_getIndex"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "lists_setIndex"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "lists_getSublist"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "lists_split"
        //         },
        //         {
        //             "kind": "BLOCK",
        //             "type": "lists_sort"
        //         },
        //     ]
        // },
    ]
};