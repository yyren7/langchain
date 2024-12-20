class BlockSettings {
    static defineBlockSettings() {
        let self = this;      
        // カスタムテキストフィールドの定義
        Blockly.FieldBlockId = class extends Blockly.Field {
          constructor(text, opt_validator) {
            super(text, opt_validator);
          }
        };
        
        Blockly.Blocks['set_output_wait'] = {
          init: function() {
            this.customId = 'set_output_wait' + '_' + self.getBlockCount('set_output_wait'); 
            this.appendDummyInput()
                .appendField("set")
                .appendField(new Blockly.FieldDropdown([["output1","1"], ["output2","2"], ["output3","3"]]), "output_list")
                .appendField(new Blockly.FieldDropdown([["ON","on"], ["OFF","off"]]), "out_state_list")
                .appendField("wait until")
                .appendField(new Blockly.FieldDropdown([["none","none"], ["input1","1"], ["input2","2"], ["input3","3"]]), "input_list")
                .appendField("=")
                .appendField(new Blockly.FieldDropdown([["none","none"], ["ON","on"], ["OFF","off"]]), "in_state_list");
                // .appendField(new Blockly.FieldBlockId('No.' + self.getBlockCount('set_output_wait')))
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(120);
         this.setTooltip("");
         this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['set_output_during'] = {
          init: function() {
            this.customId = 'set_output_during' + '_' + self.getBlockCount('set_output_during'); 
            this.appendDummyInput()
                .appendField("set")
                .appendField(new Blockly.FieldDropdown([["output1","1"], ["output2","2"], ["output3","3"]]), "output_list")
                .appendField(new Blockly.FieldDropdown([["ON","on"], ["OFF","off"]]), "state_list")
                .appendField("during")
                .appendField(new Blockly.FieldDropdown([["100","100"], ["300","300"], ["500","500"], ["1000","1000"]]), "timer_list")
                .appendField("msec")
                // .appendField(new Blockly.FieldBlockId('No.' + self.getBlockCount('set_output_during')))
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(120);
         this.setTooltip("");
         this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['wait_input'] = {
          init: function() {
            this.customId = 'wait_input' + '_' + self.getBlockCount('wait_input'); 
            this.appendDummyInput()
                .appendField("wait until")
                .appendField(new Blockly.FieldDropdown([["input1","1"], ["input2","2"], ["input3","3"]]), "input_list")
                .appendField("=")
                .appendField(new Blockly.FieldDropdown([["ON","on"], ["OFF","off"]]), "in_state_list");
                // .appendField(new Blockly.FieldBlockId('No.' + self.getBlockCount('wait_input')));
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(120);
         this.setTooltip("");
         this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['moveL'] = {
          options: [
            ["Select", "P1"]
          ],
          init: function() {
            this.customId = 'moveL_' + self.getBlockCount('moveL'); 
            this.appendDummyInput()
                .appendField("moveL to")
                .appendField(new Blockly.FieldDropdown(this.options), "point_name_list")
                // .appendField("offset:")
                .appendField(new Blockly.FieldDropdown([["without pallet","none"],
                                                        ["in pallet 1","1"], 
                                                        ["in pallet 2","2"], 
                                                        ["in pallet 3","3"], 
                                                        ["in pallet 4","4"], 
                                                        ["in pallet 5","5"], 
                                                        ["in pallet 6","6"], 
                                                        ["in pallet 7","7"], 
                                                        ["in pallet 8","8"], 
                                                        ["in pallet 9","9"], 
                                                        ["in pallet 10","10"], ]), "pallet_list");
                // .appendField(new Blockly.FieldBlockId('No.' + self.getBlockCount('moveL')));
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(10);
            this.setTooltip("");
            this.setHelpUrl("");
          }
        };
            
        Blockly.Blocks['return'] = {
          init: function() {
            this.customId = 'return_' + self.getBlockCount('return'); 
            this.appendDummyInput()
                .appendField("return to loop start");
                // .appendField(new Blockly.FieldBlockId('No.' + self.getBlockCount('return')));
            this.setPreviousStatement(true, null);
            this.setColour(200);
            this.setTooltip("");
            this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['select_robot'] = {
          init: function() {
            this.customId = 'select_robot_' + self.getBlockCount('select_robot'); 
            this.appendDummyInput()
                .appendField("select");
            this.appendEndRowInput()
                .appendField(new Blockly.FieldDropdown([["IAI 3AXIS-TABLETOP","iai_3axis_tabletop"],
                                                        ["IAI 4AXIS-TABLETOP","iai_4axis_tabletop"],
                                                        ["Dobot MG400","dobot_mg400"],
                                                        ["YAMAHA SCARA","yamaha_scara"]]), "robot_name_list")
                .appendField("as robot");
                // .appendField(new Blockly.FieldBlockId('No.' + self.getBlockCount('select_robot')));
            this.setNextStatement(true, null);
            this.setColour(10);
            this.setTooltip("");
            this.setHelpUrl("");
          },
        };
    
        Blockly.Blocks['start_thred'] = {
          func_customId: [
            ["Select","func1"]
          ],
          init: function() {
            this.customId = 'start_thred' + '_' + self.getBlockCount('start_thred'); 
            this.appendDummyInput()
                .appendField("start thread after")
                .appendField(new Blockly.FieldDropdown(this.func_customId), "func_list")
                .appendField("= ON");
                // .appendField(new Blockly.FieldBlockId('No.' + self.getBlockCount('start_thred')));
                this.appendStatementInput("DO")
                .setCheck(null);
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(315);
            this.setTooltip("");
            this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['loop'] = {
          init: function() {
            this.customId = 'loop' + '_' + self.getBlockCount('loop'); 
            this.appendDummyInput()
                .appendField("loop");
                // .appendField(new Blockly.FieldBlockId('No.' + self.getBlockCount('loop')));
            this.appendStatementInput("DO")
                .setCheck(null);
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(200);
            this.setTooltip("");
            this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['set_motor'] = {
          init: function() {
            this.customId = 'set_motor' + '_' + self.getBlockCount('set_motor'); 
            this.appendDummyInput()
                .appendField("set motor ")
                .appendField(new Blockly.FieldDropdown([["ON","on"], ["OFF","off"]]), "state_list");
                // .appendField(new Blockly.FieldBlockId('No.' + self.getBlockCount('set_motor')));
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(10);
            this.setTooltip("");
            this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['set_flag'] = {
          init: function() {
            this.customId = 'set_flag' + '_' + self.getBlockCount('set_flag'); 
            this.appendDummyInput()
                .appendField("set flag")
                .appendField(new Blockly.FieldBlockId('No.' + self.getBlockCount('set_flag')))
                .appendField("ON");
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(315);
            this.setTooltip("");
            this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['origin'] = {
          init: function() {
            this.customId = 'origin' + '_' + self.getBlockCount('origin'); 
            this.appendDummyInput()
                .appendField("move origin");
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(10);
         this.setTooltip("");
         this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['wait_end'] = {
          func_customId: [
            ["Select","func1"]
          ],
          init: function() {
            this.customId = 'wait_end' + '_' + self.getBlockCount('wait_end'); 
            this.appendDummyInput()
                .appendField("wait until")
                .appendField(new Blockly.FieldDropdown(this.func_customId), "func_list")
                .appendField("= ON");
                // .appendField(new Blockly.FieldBlockId('No.' + self.getBlockCount('wait_end')));
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(315);
            this.setTooltip("");
            this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['set_pallet'] = {
          options: [
            ["Select", "P1"]
          ],
          init: function() {
            this.customId = 'set_pallet' + '_' + self.getBlockCount('set_pallet'); 
            this.appendDummyInput()
                .appendField("set pallet ")
                .appendField("No.:")
                .appendField(new Blockly.FieldDropdown([["1","1"], 
                                                        ["2","2"],
                                                        ["3","3"],
                                                        ["4","4"],
                                                        ["5","5"],
                                                        ["6","6"],
                                                        ["7","7"],
                                                        ["8","8"],
                                                        ["9","9"],
                                                        ["10","10"]]), "no_list")
                .appendField("row:")
                .appendField(new Blockly.FieldDropdown([["2","2"],
                                                        ["3","3"],
                                                        ["4","4"],
                                                        ["5","5"],
                                                        ["6","6"],
                                                        ["7","7"],
                                                        ["8","8"],
                                                        ["9","9"],
                                                        ["10","10"]]), "row_list")
                .appendField("col:")
                .appendField(new Blockly.FieldDropdown([["2","2"],
                                                        ["3","3"],
                                                        ["4","4"],
                                                        ["5","5"],
                                                        ["6","6"],
                                                        ["7","7"],
                                                        ["8","8"],
                                                        ["9","9"],
                                                        ["10","10"]]), "col_list")
                .appendField("A:")
                .appendField(new Blockly.FieldDropdown(this.options), "A_list")
                .appendField("B:")
                .appendField(new Blockly.FieldDropdown(this.options), "B_list")
                .appendField("C:")
                .appendField(new Blockly.FieldDropdown(this.options), "C_list")
                .appendField("D:")
                .appendField(new Blockly.FieldDropdown(this.options), "D_list");
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(260);
            this.setTooltip("");
            this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['move_next_pallet'] = {
          init: function() {
            this.customId = 'move_next_pallet' + '_' + self.getBlockCount('move_next_pallet'); 
            this.appendDummyInput()
                .appendField("move on to next pocket in pallet")
                .appendField(new Blockly.FieldDropdown([["1","1"], 
                                                        ["2","2"],
                                                        ["3","3"],
                                                        ["4","4"],
                                                        ["5","5"],
                                                        ["6","6"],
                                                        ["7","7"],
                                                        ["8","8"],
                                                        ["9","9"],
                                                        ["10","10"]]), "no_list")
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(260);
            this.setTooltip("");
            this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['reset_pallet'] = {
          init: function() {
            this.customId = 'reset_pallet' + '_' + self.getBlockCount('reset_pallet'); 
            this.appendDummyInput()
                .appendField("reset pallet")
                .appendField(new Blockly.FieldDropdown([["1","1"], 
                                                        ["2","2"],
                                                        ["3","3"],
                                                        ["4","4"],
                                                        ["5","5"],
                                                        ["6","6"],
                                                        ["7","7"],
                                                        ["8","8"],
                                                        ["9","9"],
                                                        ["10","10"]]), "no_list")
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(260);
            this.setTooltip("");
            this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['check_pallet'] = {
          init: function() {
            this.appendDummyInput()
                .appendField("P&P count")
                .appendField(new Blockly.FieldDropdown([["=","="], 
                                                        [">=",">="], 
                                                        ["<=","<="], 
                                                        [">",">"], 
                                                        ["<","<"]]), "equation_list")
                .appendField(new Blockly.FieldDropdown([["MAX","max"], 
                                                        ["1","1"], ["2","2"], ["3","3"], ["4","4"], ["5","5"], ["6","6"], ["7","7"], ["8","8"], ["9","9"], ["10","10"], 
                                                        ["11","11"], ["12","12"], ["13","3"], ["14","14"], ["15","15"], ["16","16"], ["17","17"], ["18","18"], ["19","19"], ["20","20"],
                                                        ]), "cnt_list")
                .appendField("in pallet")
                .appendField(new Blockly.FieldDropdown([["1","1"], 
                                                        ["2","2"],
                                                        ["3","3"],
                                                        ["4","4"],
                                                        ["5","5"],
                                                        ["6","6"],
                                                        ["7","7"],
                                                        ["8","8"],
                                                        ["9","9"],
                                                        ["10","10"]]), "no_list");
            this.setInputsInline(true);
            this.setOutput(true, "Boolean");
            this.setColour(260);
         this.setTooltip("");
         this.setHelpUrl("");
          }
        };
    
    
        Blockly.Blocks['wait_during'] = {
          init: function() {
            this.customId = 'wait_during' + '_' + self.getBlockCount('wait_during'); 
            this.appendDummyInput()
                .appendField("wait until")
                .appendField(new Blockly.FieldDropdown([["100","100"], ["300","300"], ["500","500"], ["1000","1000"]]), "timer_list")
                .appendField("msec")
                // .appendField(new Blockly.FieldBlockId('No.' + self.getBlockCount('wait_during')))
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(200);
            this.setTooltip("");
            this.setHelpUrl("");
          }
        };
    
        Blockly.Blocks['hand_pick'] = {
          init: function() {
            this.customId = 'hand_pick' + '_' + self.getBlockCount('hand_pick'); 
            this.appendDummyInput()
                .appendField("pick with")
                .appendField(new Blockly.FieldDropdown([["single SOL suction","single_SOL_suction"], 
                                                        ["double SOL suction","double_SOL_suction"], 
                                                        ["single SOL chuck","single_SOL_chuck"], 
                                                        ["double SOL chuck","double_SOL_chuck"]]), "hand_type_list");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(160);
            this.setTooltip("type:\n single SOL suction:\n  Capture:IN1, Pick&Place:OUT1\n double SOL suction:\n  Capture:IN1, Pick:OUT1, Place:OUT2\n single SOL chuck:\n  Open:IN1, Close:IN2, Pick&Place:OUT1\n double SOL chuck:\n  Open:IN1, Close:IN2, Pick:OUT1, Place:OUT2\n");
            this.setHelpUrl("");
            // this.setCommentText("");
          }
        };
    
        Blockly.Blocks['hand_place'] = {
          init: function() {
            this.customId = 'hand_place' + '_' + self.getBlockCount('hand_place'); 
            this.appendDummyInput()
                .appendField("place with")
                .appendField(new Blockly.FieldDropdown([["single SOL suction","single_SOL_suction"], 
                                                        ["double SOL suction","double_SOL_suction"], 
                                                        ["single SOL chuck","single_SOL_chuck"], 
                                                        ["double SOL chuck","double_SOL_chuck"]]), "hand_type_list");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(160);
            this.setTooltip("type:\n single SOL suction:\n  Capture:IN1, Pick&Place:OUT1\n double SOL suction:\n  Capture:IN1, Pick:OUT1, Place:OUT2\n single SOL chuck:\n  Open:IN1, Close:IN2, Pick&Place:OUT1\n double SOL chuck:\n  Open:IN1, Close:IN2, Pick:OUT1, Place:OUT2\n");
            this.setHelpUrl("");
            // this.setCommentText("");
          }
        };
        
        // 既存ブロックにメンバ変数追加
        Blockly.Blocks['controls_whileUntil'].customId = 'controls_whileUntil' + '_' + self.getBlockCount('controls_whileUntil');
        Blockly.Blocks['controls_if'].customId = 'controls_if' + '_' + self.getBlockCount('controls_if');
    }
}