// ツールボックスの定義 
const toolbox = {
    "contents": [
        {
            // オリジナル
            "kind": "CATEGORY",
            "name": "Robot",
            "colour": 200,
            "contents": [
                {
                    "kind": "BLOCK",
                    "type": "startrobot"
                },
                {
                   "kind": "BLOCK",
                   "type": "moveabsline"
                },
                {
                    "kind": "BLOCK",
                    "type": "return"
                 },
                 {
                    "kind": "BLOCK",
                    "type": "controls_if"
                 },
            ]
        },
        // デフォルト
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
        {
        "kind": "CATEGORY",
        "name": "Loop",
        "colour": 40,
        "contents": [
            {
                "kind": "BLOCK",
                "type": "controls_repeat_ext"
            },
            {
                "kind": "BLOCK",
                "type": "controls_whileUntil"
            },
            {
                "kind": "BLOCK",
                "type": "controls_for"
            },
            {
                "kind": "BLOCK",
                "type": "controls_forEach"
            },
            {
                "kind": "BLOCK",
                "type": "controls_flow_statements"
            },
        ]
        },
        {
            "kind": "CATEGORY",
            "name": "Math",
            "colour": 70,
            "contents": [
                {
                    "kind": "BLOCK",
                    "type": "math_number"
                },
                {
                    "kind": "BLOCK",
                    "type": "math_arithmetic"
                },
                {
                    "kind": "BLOCK",
                    "type": "math_single"
                },
                {
                    "kind": "BLOCK",
                    "type": "math_trig"
                },
                {
                    "kind": "BLOCK",
                    "type": "math_constant"
                },
                {
                    "kind": "BLOCK",
                    "type": "math_number_property"
                },
                {
                    "kind": "BLOCK",
                    "type": "math_on_list"
                },
                {
                    "kind": "BLOCK",
                    "type": "math_modulo"
                },
                {
                    "kind": "BLOCK",
                    "type": "math_round"
                },
                {
                    "kind": "BLOCK",
                    "type": "math_constrain"
                },
                {
                    "kind": "BLOCK",
                    "type": "math_random_int"
                },
                {
                    "kind": "BLOCK",
                    "type": "math_random_float"
                },
                {
                    "kind": "BLOCK",
                    "type": "math_atan2"
                },
            ]
        },
        {
            "kind": "CATEGORY",
            "name": "Text",
            "colour": 100,
            "contents": [
                {
                    "kind": "BLOCK",
                    "type": "text"
                },
                {
                    "kind": "BLOCK",
                    "type": "text_join"
                },
                {
                    "kind": "BLOCK",
                    "type": "text_append"
                },
                {
                    "kind": "BLOCK",
                    "type": "text_length"
                },
                {
                    "kind": "BLOCK",
                    "type": "text_isEmpty"
                },
                {
                    "kind": "BLOCK",
                    "type": "text_indexOf"
                },
                {
                    "kind": "BLOCK",
                    "type": "text_charAt"
                },
                {
                    "kind": "BLOCK",
                    "type": "text_getSubstring"
                },
                {
                    "kind": "BLOCK",
                    "type": "text_changeCase"
                },
                {
                    "kind": "BLOCK",
                    "type": "text_trim"
                },
                {
                    "kind": "BLOCK",
                    "type": "text_print"
                },
                {
                    "kind": "BLOCK",
                    "type": "text_prompt_ext"
                },
            ]
        },
        {
            "kind": "CATEGORY",
            "name": "List",
            "colour": 140,
            "contents": [
                {
                    "kind": "BLOCK",
                    "type": "lists_create_with"
                },
                {
                    "kind": "BLOCK",
                    "type": "lists_repeat"
                },
                {
                    "kind": "BLOCK",
                    "type": "lists_length"
                },
                {
                    "kind": "BLOCK",
                    "type": "lists_isEmpty"
                },
                {
                    "kind": "BLOCK",
                    "type": "lists_indexOf"
                },
                {
                    "kind": "BLOCK",
                    "type": "lists_getIndex"
                },
                {
                    "kind": "BLOCK",
                    "type": "lists_setIndex"
                },
                {
                    "kind": "BLOCK",
                    "type": "lists_getSublist"
                },
                {
                    "kind": "BLOCK",
                    "type": "lists_split"
                },
                {
                    "kind": "BLOCK",
                    "type": "lists_sort"
                },
            ]
        },
    ]
};