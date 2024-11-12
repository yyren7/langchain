class BlockUtility {
  constructor() {
    this.blockCount = {}; 
    this.all_block_flow = []; 
  }

  // ブロックの数を返すメソッド
  getBlockCount(type) {
    return this.blockCount[type] || 1;
  }

  // ブロックの数を更新するメソッド
  updateBlockCount(type, increment = 1) {
    this.blockCount[type] = (this.blockCount[type] || 1) + increment;
  }

  getBlockPosition(custom_id, all_block_flow){
    for (let i = 0; i < all_block_flow.length; i++) {
      for (let j = 0; j < all_block_flow[i].length; j++) {
        if(all_block_flow[i][j].custom_id === custom_id){
          return {
            thread_no: i, 
            flow_no: j, 
        };
        }
      }
    }
    return {
      thread_no: -1, 
      flow_no: -1, 
    };
  }
}

BU_instance = new BlockUtility();

class BlockFlow {
  // クラス変数定義
  static setJson(json_data) {
    BlockFlow.json_data = json_data;
  }

  static setRelay(MR_relay) {
    BlockFlow.MR_relay = MR_relay;
  }

  static setMotionParam(override=100) {
    BlockFlow.override = override;
  }

  constructor() {
    // ブロックの形を定義
    const block_form = new BlockForm();
    block_form.defineBlockForm();
    
    // ブロックが生成するコードを定義
    const block_code = new BlockCode();
    block_code.defineBlockCode();

    // ブロックが追加される度に行う動作を定義
    this.addBlockListener();
    this.deleteBlockListener();
  }

  // ブロック追加のイベントリスナーを設定するメソッド
  addBlockListener() {
    const self = this; // thisの値を安定化させる
    Blockly.getMainWorkspace().addChangeListener(function (event) {
      if (event.type === Blockly.Events.BLOCK_CREATE) {
        const block = Blockly.getMainWorkspace().getBlockById(event.blockId);
        BU_instance.updateBlockCount(block.type); // ブロックの数を更新
      }
    });
  }

  deleteBlockListener() {
    const self = this; // thisの値を安定化させる  
    Blockly.getMainWorkspace().addChangeListener(function (event) {
      if (event.type === Blockly.Events.BLOCK_DELETE) { // ブロックが削除された場合のみ処理を行う
        const oldXml = event.oldXml;
        if (oldXml && oldXml.tagName === 'block') {
          const type = oldXml.getAttribute('type');
          // BU_instance.updateBlockCount(type, -1);
        }
      }
    });
  }

  checkBlockId(process_flow, block_id) {
    let key = block_id;
    let key_index = -1;
    for (let j = 0; j < process_flow.length; j++) {
      if (key === process_flow[j].id){
        key_index = j;
      }
    }  
    return key_index;
  }

  convNum2Device(seq_number, offset){
    const word_no = Math.floor(seq_number / 100) + Math.floor(offset / 16)
    const bit_no  = (seq_number % 100) + (offset % 16)
    const relay_no = word_no * 100 + bit_no
    return relay_no;
  }

  getPreviousBlockId(blocks, blockId) {
    for (let i = 0; i < blocks.length; i++) {
        let block = blocks[i];
        if (block.getAttribute("id") === blockId) {
            let parentBlock = block.parentNode;
            while (parentBlock) {
                if ((parentBlock.tagName === "block") && 
                  ((parentBlock.getAttribute("type") != 'logic_boolean') &&
                    (parentBlock.getAttribute("type") != 'text') && 
                    (parentBlock.getAttribute("type") != 'check_pallet'))) {
                    return parentBlock.getAttribute("id");
                }
                parentBlock = parentBlock.parentNode; // 親をたどる
            }
            break;
        }
    }
    return null; // 前に接続されたブロックが見つからない場合
  }

  convertXMLtoArray(xml) {
    let blocks = xml.getElementsByTagName("block");
    let all_block_flow = [];
    let block_flow = [];
    let block_cnt = 0;
    let init_start_addr = 0;
    let init_stop1_addr = 1000;
    let init_stop2_addr = 2000;
    let init_stop3_addr = 3000;

    // ブロックの走査
    for (let i = 0; i < blocks.length; i++) {
      let block_contents = [];
      let block = blocks[i];
      let onset1_contents = [];
      let onset_contents = [];
      let block_type = block.getAttribute("type");
      let block_id = block.getAttribute("id");
      let custom_block_id = workspace.getBlockById(block_id).customId;
      // 条件ブロック以外なら
      if((block_type != 'logic_boolean') && (block_type != 'text') && (block_type != 'check_pallet')){        
        ///////////////////////////////////
        // 当該情報
        ///////////////////////////////////
        block_contents.type = block_type;
        block_contents.id = block_id;
        if(custom_block_id) block_contents.custom_id = custom_block_id;
        else block_contents.custom_id = block_type;
      
        console.log('--------------------------------------------');
        
        ///////////////////////////////////
        // 接続元情報
        ///////////////////////////////////
        // 変数定義
        let parent_tag = block.parentNode.tagName;
        let key_index = 0;
        let key = '';

        switch (parent_tag) {
          // 最初のブロックなら 
          case 'xml':
            if(i > 0){
              all_block_flow.push(block_flow);
              block_flow = [];
            }
            // サブプロセス開始ブロックなら
            if(block_type != 'start_thred'){
              onset_contents.push(992002);
              block_contents.onset1 = onset_contents;
            }
            break;
          // 接続元ブロックが内包ブロックなら
          case 'statement':
            // elseifとelseの数をカウント
            let children = block.parentNode.parentNode.childNodes;
            let index = 0;
            let elseif_cnt = 0;
            let else_cnt = 0;
            for(let element of children) {
              let child_tag = children[index].nodeName;
              if(child_tag === 'mutation'){
                if(children[index].getAttribute('elseif') != null){
                  elseif_cnt = Number(children[index].getAttribute('elseif'));
                }
                if(children[index].getAttribute('else') != null){
                  else_cnt = Number(children[index].getAttribute('else'));
                }
                break;
              }
              index++;
            }
            let branch_cnt = elseif_cnt+else_cnt;

            // 接続元ブロックの要素番号算出
            key_index = 0;
            key = block.parentNode.parentNode.getAttribute('id');
            key_index = this.checkBlockId(block_flow, key);

            // 内包ブロックのどの領域が接続元か確認
            switch(block.parentNode.getAttribute('name')){
              case 'DO':
                onset_contents.push(block_flow[key_index].stop1);
                block_contents.onset1 = onset_contents;
                break;
              case 'DO0':
                onset_contents.push(block_flow[key_index].stop1);
                block_contents.onset1 = onset_contents;
                break;
              case 'DO1':
                onset_contents.push(block_flow[key_index].stop2);
                block_contents.onset1 = onset_contents;
                break;
              case 'DO2':
                onset_contents.push(block_flow[key_index].stop3);
                block_contents.onset1 = onset_contents;
                break;
              case 'ELSE':
                if (branch_cnt === 1) 
                {
                  onset_contents.push(block_flow[key_index].stop2);
                  block_contents.onset1 = onset_contents;
                  // block_contents.onset2 = onset_contents;
                }
                if (branch_cnt === 2) {
                  onset_contents.push(block_flow[key_index].stop3);
                  block_contents.onset1 = onset_contents;
                  // block_contents.onset3 = onset_contents;
                }
                break;
            }
            break;

        // 接続元が通常のブロックなら
        case 'next':
          // 接続元ブロックがifじゃないこと確認
          let previousBlockId = this.getPreviousBlockId(blocks, block.id);
          let previousBlockType = workspace.getBlockById(previousBlockId).type;
          // 1つ前のブロックが if ならwhileを継続
          while (previousBlockType.includes('controls_if')){
            console.log('post', previousBlockType);
            previousBlockId = this.getPreviousBlockId(blocks, previousBlockId);
            previousBlockType = workspace.getBlockById(previousBlockId).type;
          }
          // 接続元ブロックの要素番号算出
          key_index = 0;
          key = previousBlockId;
          key_index = this.checkBlockId(block_flow, key);  
          onset_contents.push(block_flow[key_index].stop1);
          // サブプロセス開始ブロックなら
          if(block_type != 'start_thred'){
            block_contents.onset1 = onset_contents; 
          }
          break;
        default:
        }

        ///////////////////////////////////
        // 当該情報
        ///////////////////////////////////
        block_contents.start = this.convNum2Device(init_start_addr, block_cnt);
        block_contents.stop1 = this.convNum2Device(init_stop1_addr,  block_cnt);

        ///////////////////////////////////
        // 接続先情報
        ///////////////////////////////////
        let children = block.childNodes;
        let index = 0;
        let elseif_cnt = 0;
        let else_cnt = 0;
      
        for(let element of children) {
          let child_tag = children[index].nodeName;
          if(child_tag === 'mutation'){
            if(children[index].getAttribute('elseif') != null){
              elseif_cnt = Number(children[index].getAttribute('elseif'));
            }
            if(children[index].getAttribute('else') != null){
              else_cnt = Number(children[index].getAttribute('else'));
            }
            break;
          }
          index++;
        }
        
        // アドレス設定
        let branch_cnt = elseif_cnt+else_cnt;
        switch(branch_cnt){
          case 1:
            block_contents.stop1 = this.convNum2Device(init_stop1_addr, block_cnt);
            block_contents.stop2 = this.convNum2Device(init_stop2_addr, block_cnt);
            break;
          case 2:
            block_contents.stop1 = this.convNum2Device(init_stop1_addr, block_cnt);
            block_contents.stop2 = this.convNum2Device(init_stop2_addr, block_cnt);
            block_contents.stop3 = this.convNum2Device(init_stop3_addr, block_cnt);
            break;
        }
        // ブロック情報をブロック配列に格納
        block_flow.push(block_contents);
      }
      // 全体のブロックフローに追加
      if(i === blocks.length-1){
        all_block_flow.push(block_flow);
        block_flow = [];
      }
      block_cnt = block_cnt + 1;
    } 

    ///////////////////////////////////
    // リセットの追加
    ///////////////////////////////////
    for (let i = 0; i < all_block_flow.length; i++) {
      // loopの場所を確認
      let found_loop_index = -1;
      for (let j = 0; j < all_block_flow[i].length; j++) {
        let block_type = workspace.getBlockById(all_block_flow[i][j].id).type;
        if ((block_type.includes('controls_whileUntil')) || (block_type.includes('loop'))){
          found_loop_index = j;
          break;
        }
      }
      // returnの場所を確認し、loopにリセットアドレスを追加
      if (found_loop_index >= 0){
        let reset_contents = [];
        for (let j = 0; j < all_block_flow[i].length; j++) {
          let block_type = workspace.getBlockById(all_block_flow[i][j].id).type;
          if (block_type.includes('return')){
            reset_contents.push(all_block_flow[i][j].stop1);
          }
        }
        all_block_flow[i][found_loop_index].reset = reset_contents;
      }
    }

    ///////////////////////////////////
    // filedタグの追加（ブロックを定義した段階では field タグが存在しないので、getFieldValue()は使えない）
    ///////////////////////////////////
    const local_wk = Blockly.getMainWorkspace();
    local_wk.getAllBlocks().forEach(block => {
      let  contents = [];
      if ((block.type === 'wait_end') || (block.type === 'start_thred')) {
        const dropdownField = block.getField('func_list');
        const target_block_customId = dropdownField.value_;
        const target_block_pos = BU_instance.getBlockPosition(target_block_customId, BU_instance.all_block_flow);
        const this_block_pos = BU_instance.getBlockPosition(block.customId, BU_instance.all_block_flow);;
        // 自身と対象のブロックが存在するなら
        if ((target_block_pos.thread_no >= 0) && (target_block_pos.flow_no >= 0) &&
            (target_block_pos.thread_no < all_block_flow.length) && (target_block_pos.flow_no < all_block_flow[target_block_pos.thread_no].length) && 
            (this_block_pos.thread_no >= 0) && (this_block_pos.flow_no >= 0) &&
            (this_block_pos.thread_no < all_block_flow.length) && (this_block_pos.flow_no < all_block_flow[this_block_pos.thread_no].length)){
          contents.push(all_block_flow[target_block_pos.thread_no][target_block_pos.flow_no].stop1);
          if(block.type === 'wait_end'){
            all_block_flow[this_block_pos.thread_no][this_block_pos.flow_no].end1 = contents;
          }
          else if(block.type === 'start_thred'){
            all_block_flow[this_block_pos.thread_no][this_block_pos.flow_no].onset1 = contents;
          }
        }
      }
    });

    // デバッグ用ログ出力
    let all_block_flow_buf = all_block_flow;
    all_block_flow_buf.forEach(obj => {
      const filteredObj = {};
      for (const key in obj) {
        delete obj[key].type;
        delete obj[key].id;
        filteredObj[key] = obj[key];
      }
      console.log(filteredObj);
    });

    return all_block_flow;
  }

  updateBlock(){  
    // console.log("MR", BlockFlow.MR_relay);

    //////////////////////////////////////////////////
    // ブロックのフロー作成
    //////////////////////////////////////////////////  
    let workspace = Blockly.getMainWorkspace();
    let xml = Blockly.Xml.workspaceToDom(workspace);
    let xmlString = Blockly.Xml.domToPrettyText(xml);
    BU_instance.all_block_flow = this.convertXMLtoArray(xml);
    // console.log(BU_instance.all_block_flow);
    // console.log(xmlString);

    //////////////////////////////////////////////////
    // 引数名更新の前処理
    //////////////////////////////////////////////////
    this.options = [];
    for (let key in BlockFlow.json_data) {
      this.options.push([BlockFlow.json_data[key]['name'], key]);
    }

    //////////////////////////////////////////////////
    // set_flagの引数名を更新
    //////////////////////////////////////////////////
    this.func_customId = [];
    for (let i = 0; i < BU_instance.all_block_flow.length; i++) {
      for (let j = 0; j < BU_instance.all_block_flow[i].length; j++) {
        // set_flagブロックなら
        const target_block_customId = BU_instance.all_block_flow[i][j].custom_id;
        if ((target_block_customId.includes('set_flag'))) {
          const arg_name_list = BU_instance.all_block_flow[i][j].custom_id.split("_");
          const no = arg_name_list[arg_name_list.length-1];
          this.func_customId.push(['flag No.' + no, BU_instance.all_block_flow[i][j].custom_id]);
        }
      }
    }

    //////////////////////////////////////////////////
    // その他関数の引数名を更新
    //////////////////////////////////////////////////
    const local_wk = Blockly.getMainWorkspace();
    local_wk.getAllBlocks().forEach(block => {
      if (block.type === 'moveL') {
        const dropdownField = block.getField('point_name_list');
        if (dropdownField) {
          dropdownField.menuGenerator_ = this.options;
        }
      }
      if (block.type === 'wait_end') {
        const dropdownField = block.getField('func_list');
        if (dropdownField) {
          dropdownField.menuGenerator_ = this.func_customId;
        }
      }
      if (block.type === 'start_thred') {
        const dropdownField = block.getField('func_list');
        if (dropdownField) {
          dropdownField.menuGenerator_ = this.func_customId;
        }
      }
      if (block.type === 'set_pallet') {
        const dropdownField_A = block.getField('A_list');
        if (dropdownField_A) {
          dropdownField_A.menuGenerator_ = this.options;
        }
        const dropdownField_B = block.getField('B_list');
        if (dropdownField_B) {
          dropdownField_B.menuGenerator_ = this.options;
        }
        const dropdownField_C = block.getField('C_list');
        if (dropdownField_C) {
          dropdownField_C.menuGenerator_ = this.options;
        }
        const dropdownField_D = block.getField('D_list');
        if (dropdownField_D) {
          dropdownField_D.menuGenerator_ = this.options;
        }
      }
    });
  }
}

class BlockForm{
  constructor() {
  }
  defineBlockForm() {
      let self = this;      
      // カスタムテキストフィールドの定義
      Blockly.FieldBlockId = class extends Blockly.Field {
        constructor(text, opt_validator) {
          super(text, opt_validator);
        }
      };

      
      Blockly.Blocks['set_output_wait'] = {
        init: function() {
          this.customId = 'set_output_wait' + '_' + BU_instance.getBlockCount('set_output_wait'); 
          this.appendDummyInput()
              .appendField("set")
              .appendField(new Blockly.FieldDropdown([["output1","1"], ["output2","2"], ["output3","3"]]), "output_list")
              .appendField(new Blockly.FieldDropdown([["ON","on"], ["OFF","off"]]), "out_state_list")
              .appendField("wait until")
              .appendField(new Blockly.FieldDropdown([["none","none"], ["input1","1"], ["input2","2"], ["input3","3"]]), "input_list")
              .appendField("=")
              .appendField(new Blockly.FieldDropdown([["none","none"], ["ON","on"], ["OFF","off"]]), "in_state_list");
              // .appendField(new Blockly.FieldBlockId('No.' + BU_instance.getBlockCount('set_output_wait')))
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
          this.customId = 'set_output_during' + '_' + BU_instance.getBlockCount('set_output_during'); 
          this.appendDummyInput()
              .appendField("set")
              .appendField(new Blockly.FieldDropdown([["output1","1"], ["output2","2"], ["output3","3"]]), "output_list")
              .appendField(new Blockly.FieldDropdown([["ON","on"], ["OFF","off"]]), "state_list")
              .appendField("during")
              .appendField(new Blockly.FieldDropdown([["100","100"], ["300","300"], ["500","500"], ["1000","1000"]]), "timer_list")
              .appendField("msec")
              // .appendField(new Blockly.FieldBlockId('No.' + BU_instance.getBlockCount('set_output_during')))
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
          this.customId = 'wait_input' + '_' + BU_instance.getBlockCount('wait_input'); 
          this.appendDummyInput()
              .appendField("wait until")
              .appendField(new Blockly.FieldDropdown([["input1","1"], ["input2","2"], ["input3","3"]]), "input_list")
              .appendField("=")
              .appendField(new Blockly.FieldDropdown([["ON","on"], ["OFF","off"]]), "in_state_list");
              // .appendField(new Blockly.FieldBlockId('No.' + BU_instance.getBlockCount('wait_input')));
          this.setInputsInline(true);
          this.setPreviousStatement(true, null);
          this.setNextStatement(true, null);
          this.setColour(120);
       this.setTooltip("");
       this.setHelpUrl("");
        }
      };
  
      Blockly.Blocks['moveL'] = {
        init: function() {
          this.options = [];
          for (let key in BlockFlow.json_data) {
            this.options.push([BlockFlow.json_data[key]['name'], key]);
          }
          this.customId = 'moveL_' + BU_instance.getBlockCount('moveL'); 
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
              // .appendField(new Blockly.FieldBlockId('No.' + BU_instance.getBlockCount('moveL')));
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
          this.customId = 'return_' + BU_instance.getBlockCount('return'); 
          this.appendDummyInput()
              .appendField("return to loop start");
              // .appendField(new Blockly.FieldBlockId('No.' + BU_instance.getBlockCount('return')));
          this.setPreviousStatement(true, null);
          this.setColour(200);
          this.setTooltip("");
          this.setHelpUrl("");
        }
      };
  
      Blockly.Blocks['select_robot'] = {
        init: function() {
          this.customId = 'select_robot_' + BU_instance.getBlockCount('select_robot'); 
          this.appendDummyInput()
              .appendField("select");
          this.appendEndRowInput()
              .appendField(new Blockly.FieldDropdown([["IAI 3AXIS-TABLETOP","iai_3axis_tabletop"],
                                                      ["IAI 4AXIS-TABLETOP","iai_4axis_tabletop"],
                                                      ["Dobot MG400","dobot_mg400"],
                                                      ["YAMAHA SCARA","yamaha_scara"]]), "robot_name_list")
              .appendField("as robot");
              // .appendField(new Blockly.FieldBlockId('No.' + BU_instance.getBlockCount('select_robot')));
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
          this.customId = 'start_thred' + '_' + BU_instance.getBlockCount('start_thred'); 
          this.appendDummyInput()
              .appendField("start thread after")
              .appendField(new Blockly.FieldDropdown(this.func_customId), "func_list")
              .appendField("= ON");
              // .appendField(new Blockly.FieldBlockId('No.' + BU_instance.getBlockCount('start_thred')));
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
          this.customId = 'loop' + '_' + BU_instance.getBlockCount('loop'); 
          this.appendDummyInput()
              .appendField("loop");
              // .appendField(new Blockly.FieldBlockId('No.' + BU_instance.getBlockCount('loop')));
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
          this.customId = 'set_motor' + '_' + BU_instance.getBlockCount('set_motor'); 
          this.appendDummyInput()
              .appendField("set motor ")
              .appendField(new Blockly.FieldDropdown([["ON","on"], ["OFF","off"]]), "state_list");
              // .appendField(new Blockly.FieldBlockId('No.' + BU_instance.getBlockCount('set_motor')));
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
          this.customId = 'set_flag' + '_' + BU_instance.getBlockCount('set_flag'); 
          this.appendDummyInput()
              .appendField("set flag")
              .appendField(new Blockly.FieldBlockId('No.' + BU_instance.getBlockCount('set_flag')))
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
          this.customId = 'origin' + '_' + BU_instance.getBlockCount('origin'); 
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
          this.customId = 'wait_end' + '_' + BU_instance.getBlockCount('wait_end'); 
          this.appendDummyInput()
              .appendField("wait until")
              .appendField(new Blockly.FieldDropdown(this.func_customId), "func_list")
              .appendField("= ON");
              // .appendField(new Blockly.FieldBlockId('No.' + BU_instance.getBlockCount('wait_end')));
          this.setInputsInline(true);
          this.setPreviousStatement(true, null);
          this.setNextStatement(true, null);
          this.setColour(315);
          this.setTooltip("");
          this.setHelpUrl("");
        }
      };
  
      Blockly.Blocks['set_pallet'] = {
        init: function() {
          this.options = [];
          for (let key in BlockFlow.json_data) {
            this.options.push([BlockFlow.json_data[key]['name'], key]);
          }
          this.customId = 'set_pallet' + '_' + BU_instance.getBlockCount('set_pallet'); 
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
          this.customId = 'move_next_pallet' + '_' + BU_instance.getBlockCount('move_next_pallet'); 
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
          this.customId = 'reset_pallet' + '_' + BU_instance.getBlockCount('reset_pallet'); 
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
          this.customId = 'wait_during' + '_' + BU_instance.getBlockCount('wait_during'); 
          this.appendDummyInput()
              .appendField("wait until")
              .appendField(new Blockly.FieldDropdown([["100","100"], ["300","300"], ["500","500"], ["1000","1000"]]), "timer_list")
              .appendField("msec")
              // .appendField(new Blockly.FieldBlockId('No.' + BU_instance.getBlockCount('wait_during')))
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
          this.customId = 'hand_pick' + '_' + BU_instance.getBlockCount('hand_pick'); 
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
          this.customId = 'hand_place' + '_' + BU_instance.getBlockCount('hand_place'); 
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
      Blockly.Blocks['controls_whileUntil'].customId = 'controls_whileUntil' + '_' + BU_instance.getBlockCount('controls_whileUntil');
      Blockly.Blocks['controls_if'].customId = 'controls_if' + '_' + BU_instance.getBlockCount('controls_if');
      Blockly.Blocks['variables_set'].customId = 'variables_set' + '_' + BU_instance.getBlockCount('variables_set');
    }
}

class BlockCode {
  constructor() {
    this.addr_str = 'MR';

  }

  getBlockAddr(blockId) {
    const block_pos = BU_instance.getBlockPosition(blockId, BU_instance.all_block_flow);
    const block_flow = BU_instance.all_block_flow[block_pos.thread_no][block_pos.flow_no];
  
    return {
      onset1_addr_list: block_flow.onset1,
      reset_addr_list: block_flow.reset,
      end_addr: block_flow.end1,
      start_addr: block_flow.start,
      stop1_addr: block_flow.stop1,
      stop2_addr: block_flow.stop2,
      stop3_addr: block_flow.stop3
    };
  }

  defineBlockCode() {
    const self = this; // thisの値を安定化させる

    python.pythonGenerator.forBlock['select_robot'] = function(block, generator) {
      //////////////////////////////////////////////////
      // アドレス参照
      //////////////////////////////////////////////////   
      const block_addr = self.getBlockAddr(block.customId); 

      //////////////////////////////////////////////////
      // 前処理
      //////////////////////////////////////////////////
      const robot_name = block.getFieldValue('robot_name_list');

      //////////////////////////////////////////////////
      // プロセス
      //////////////////////////////////////////////////
      let LF = '\n';
      let INDENT = '  ';
      let line_str = [];
      line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
      for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
        if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
        else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
      }
      if(block_addr.reset_addr_list){
        for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + `L.ANB(${self.addr_str}, ${block_addr.block_addr.reset_addr_list[i]})` + LF);
      }
      line_str.push(INDENT + INDENT + `L.MPS()` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.MPP()` + LF);
      line_str.push(INDENT + INDENT + `L.LDPB(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);

      //////////////////////////////////////////////////
      // プロセス後動作
      //////////////////////////////////////////////////
      line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
      line_str.push(INDENT + INDENT +`L.LDP(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT +`if (L.aax & L.iix):` + LF);
      line_str.push(INDENT + INDENT + INDENT + `module = importlib.import_module('${robot_name}_api')` + LF);
      line_str.push(INDENT + INDENT + INDENT + "RB = module.RobotApi('192.168.250.101', 23, '/dev/ttyUSB0', 115200)" + LF);  
      line_str.push(INDENT + INDENT +`if(RB):` + LF);
      line_str.push(INDENT + INDENT + INDENT + "RB.getRobotStatus()" + LF);  
      line_str.push(INDENT + INDENT + INDENT + "input_port = RB.getInput()" + LF);   
      line_str.push(INDENT + INDENT + INDENT + "servo = RB.servo" + LF);  
      line_str.push(INDENT + INDENT + INDENT + "origin = RB.origin" + LF);  
      line_str.push(INDENT + INDENT + INDENT + "arrived = RB.arrived" + LF);  
      line_str.push(INDENT + INDENT + INDENT + "current_pos['x'] = RB.current_pos[0]" + LF);  
      line_str.push(INDENT + INDENT + INDENT + "current_pos['y'] = RB.current_pos[1]" + LF);  
      line_str.push(INDENT + INDENT + INDENT + "current_pos['z'] = RB.current_pos[2]" + LF);  
      line_str.push(INDENT + LF);      

      return line_str.join("");
    };

    python.pythonGenerator.forBlock['start_thred'] = function(block, generator) {
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    line_str.push(INDENT + INDENT + `L.LDPB(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   
    line_str.push(INDENT + INDENT + LF);   

    let branches = ['DO'].map(label => generator.statementToCode(block, label)).join('\n');
    
    // Return the generated code
    return line_str.join("") + branches;
    };

    python.pythonGenerator.forBlock['moveL'] = function(block, generator) {  
      //////////////////////////////////////////////////
      // 前処理
      //////////////////////////////////////////////////
      const point_name = block.getFieldValue('point_name_list');
      const pallet_no = block.getFieldValue('pallet_list');
      let point_name_str = String(point_name);
      let x = BlockFlow.json_data[point_name_str]['x_pos'];
      let y = BlockFlow.json_data[point_name_str]['y_pos'];
      let z = BlockFlow.json_data[point_name_str]['z_pos'];
      let rx = BlockFlow.json_data[point_name_str]['rx_pos'];
      let ry = BlockFlow.json_data[point_name_str]['ry_pos'];
      let rz = BlockFlow.json_data[point_name_str]['rz_pos'];
      let vel = BlockFlow.json_data[point_name_str]['vel'];
      let acc = BlockFlow.json_data[point_name_str]['acc'];
      let dec = BlockFlow.json_data[point_name_str]['dec'];
      let dist = 0.1;
      let wait = 0;
      let off_rx = 0;
      let off_ry = 0;
      let off_rz = 0;
      let override = BlockFlow.override;
    
      //////////////////////////////////////////////////
      // アドレス参照
      //////////////////////////////////////////////////    
      const block_addr = self.getBlockAddr(block.customId); 

      //////////////////////////////////////////////////
      // プロセス
      //////////////////////////////////////////////////
      let LF = '\n';
      let line_str = [];
      let INDENT = '  ';
      line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
      for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
        if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
        else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
      }
      if(block_addr.reset_addr_list){
        for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
      }
      line_str.push(INDENT + INDENT + `L.MPS()` + LF);
      line_str.push(INDENT + INDENT + `L.LDB(R, 5001)` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.MPP()` + LF);
      line_str.push(INDENT + INDENT + `L.LDB(R, 5001)` + LF);
      line_str.push(INDENT + INDENT + `L.AND(arrived)` + LF);
      line_str.push(INDENT + INDENT + `L.ANPB(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);

      //////////////////////////////////////////////////
      // プロセス後動作
      //////////////////////////////////////////////////
      line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
      line_str.push(INDENT + INDENT + `L.LDP(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `if (L.aax & L.iix):` + LF);
      if(pallet_no != 'none') line_str.push(INDENT + INDENT + INDENT + `x, y, z, rx, ry, rz, vel, acc, dec, dist, wait = L.FB_setRobotParam(${x}, ${y}, ${z}, ${rx}, ${ry}, ${rz}, ${vel}, ${acc}, ${dec}, ${dist}, ${wait}, pallet_offset[${pallet_no}-1]['x'], pallet_offset[${pallet_no}-1]['y'], pallet_offset[${pallet_no}-1]['z'], 0, 0, 0, ${override})` + LF);
      else                    line_str.push(INDENT + INDENT + INDENT + `x, y, z, rx, ry, rz, vel, acc, dec, dist, wait = L.FB_setRobotParam(${x}, ${y}, ${z}, ${rx}, ${ry}, ${rz}, ${vel}, ${acc}, ${dec}, ${dist}, ${wait}, 0, 0, 0, 0, 0, 0, ${override})` + LF);
      line_str.push(INDENT + INDENT + INDENT + `RB.moveAbsoluteLine(x, y, z, rx, ry, rz, vel, acc, dec)` + LF);
      line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `if (L.aax & L.iix):` + LF);
      line_str.push(INDENT + INDENT + INDENT + `target_pos = []` + LF);
      if(pallet_no != 'none') {
        line_str.push(INDENT + INDENT + INDENT + `target_pos.append(${x}+pallet_offset[${pallet_no}-1]['x'])` + LF);
        line_str.push(INDENT + INDENT + INDENT + `target_pos.append(${y}+pallet_offset[${pallet_no}-1]['y'])` + LF);
        line_str.push(INDENT + INDENT + INDENT + `target_pos.append(${z}+pallet_offset[${pallet_no}-1]['z'])` + LF);
        line_str.push(INDENT + INDENT + INDENT + `target_pos.append(${rx})` + LF);
        line_str.push(INDENT + INDENT + INDENT + `target_pos.append(${ry})` + LF);
        line_str.push(INDENT + INDENT + INDENT + `target_pos.append(${rz})` + LF);
      }
      else{
        line_str.push(INDENT + INDENT + INDENT + `target_pos.append(${x})` + LF);
        line_str.push(INDENT + INDENT + INDENT + `target_pos.append(${y})` + LF);
        line_str.push(INDENT + INDENT + INDENT + `target_pos.append(${z})` + LF);
        line_str.push(INDENT + INDENT + INDENT + `target_pos.append(${rx})` + LF);
        line_str.push(INDENT + INDENT + INDENT + `target_pos.append(${ry})` + LF);
        line_str.push(INDENT + INDENT + INDENT + `target_pos.append(${rz})` + LF);
      }
      line_str.push(INDENT + INDENT + INDENT + `RB.waitArrive(target_pos, ${dist})` + LF);
      line_str.push(INDENT + LF);        

      return line_str.join("");
      };

    python.pythonGenerator.forBlock['return'] = function(block, generator) {
      //////////////////////////////////////////////////
      // アドレス参照
      //////////////////////////////////////////////////    
      const block_addr = self.getBlockAddr(block.customId); 

      //////////////////////////////////////////////////
      // プロセス
      //////////////////////////////////////////////////
      let LF = '\n';
      let INDENT = '  ';
      let line_str = [];
      line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
      for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
        if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
        else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
      }
      if(block_addr.reset_addr_list){
        for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
      }
      line_str.push(INDENT + INDENT + `L.MPS()` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.MPP()` + LF);
      line_str.push(INDENT + INDENT + `L.LDPB(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + LF);      

      return line_str.join("");
    };

    python.pythonGenerator.forBlock['end'] = function(block, generator) {
      var value_start = generator.valueToCode(block, 'start', python.Order.ATOMIC);
      var value_name = generator.valueToCode(block, 'NAME', python.Order.ATOMIC);
      // TODO: Assemble python into code variable.
      var code = '...';
      // TODO: Change ORDER_NONE to the correct strength.
      return [code, Blockly.python.ORDER_NONE];
    };

    python.pythonGenerator.forBlock['controls_whileUntil'] = function(block, generator) {
      //////////////////////////////////////////////////
      // アドレス参照
      //////////////////////////////////////////////////    
      const block_addr = self.getBlockAddr(block.customId);       
      //////////////////////////////////////////////////
      // シーケンス作成
      //////////////////////////////////////////////////
      let LF = '\n';
      let INDENT = '  ';
      let line_str = [];

      for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
        if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
        else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
      }
      if(block_addr.reset_addr_list){
        for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
      }
      line_str.push(INDENT + INDENT + `L.MPS()` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.MPP()` + LF);
      line_str.push(INDENT + INDENT + `L.LDPB(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + LF);      
    
      //////////////////////////////////////////////////
      // デフォルトのwhile
      //////////////////////////////////////////////////    
      var until = block.getFieldValue('MODE') == 'UNTIL';
      var argument0 = Blockly.Python.valueToCode(block, 'BOOL',
          until ? Blockly.Python.ORDER_LOGICAL_NOT :
          Blockly.Python.ORDER_NONE) || 'False';
      var branch = line_str.join("") + Blockly.Python.statementToCode(block, 'DO');
      if (until) {
        branch = 'if not ' + argument0 + ':\n' + Blockly.Python.prefixLines(branch, Blockly.Python.INDENT);
      }
      return branch;
      // return 'while ' + argument0 + ':\n' + branch;
   };

   Blockly.Python['loop'] = function(block) {
      //////////////////////////////////////////////////
      // アドレス参照
      //////////////////////////////////////////////////    
      const block_addr = self.getBlockAddr(block.customId);       
      //////////////////////////////////////////////////
      // シーケンス作成
      //////////////////////////////////////////////////
      let LF = '\n';
      let INDENT = '  ';
      let line_str = [];
      line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
      for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
        if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
        else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
      }
      if(block_addr.reset_addr_list){
        for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
      }
      line_str.push(INDENT + INDENT + `L.MPS()` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.MPP()` + LF);
      line_str.push(INDENT + INDENT + `L.LDPB(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + LF);      
      var code = line_str.join("");

      // DOステートメント以降のブロックコードを加算
      var statements_do = Blockly.Python.statementToCode(block, 'DO');  
      // 各行の先頭のインデントを削除
      statements_do = statements_do.replace(/^ {2}/gm, '');   
      // statements_do.split('\n').forEach(function(statement) {
      //   code += statement + '\n';
      // });
      return code + statements_do;
  };

  python.pythonGenerator.forBlock['set_motor'] = function(block, generator) {
    //////////////////////////////////////////////////
    // 前処理
    //////////////////////////////////////////////////
    var state = block.getFieldValue('state_list');
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    line_str.push(INDENT + INDENT + `L.LD(servo)` + LF);
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   

    //////////////////////////////////////////////////
    // プロセス後動作
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
    line_str.push(INDENT + INDENT +`L.LDP(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT +`if (L.aax & L.iix):` + LF);
    if(state === 'on')       line_str.push(INDENT + INDENT + INDENT + `RB.setServoOn()` + LF); 
    else if(state === 'off') line_str.push(INDENT + INDENT + INDENT + `RB.setServoOff()` + LF); 
    line_str.push(INDENT + LF);

    return line_str.join("");
  };

  python.pythonGenerator.forBlock['origin'] = function(block, generator) {
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    line_str.push(INDENT + INDENT + `L.LD(origin)` + LF);
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   

    //////////////////////////////////////////////////
    // プロセス後動作
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
    line_str.push(INDENT + INDENT +`L.LDP(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT +`if ((L.aax & L.iix) and not(origin)):` + LF);
    line_str.push(INDENT + INDENT + INDENT + `RB.moveOrigin()` + LF); 
    line_str.push(INDENT + LF);

    return line_str.join("");
  };

  python.pythonGenerator.forBlock['wait_end'] = function(block, generator) {
    //////////////////////////////////////////////////
    // 前処理
    //////////////////////////////////////////////////
    var dropdown_func_list = block.getFieldValue('func_list');
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    for (let i = 0; i < end_addr_list.length; i++) {
      line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.end_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   
    line_str.push(INDENT + LF); 

    return line_str.join("");
  };

  python.pythonGenerator.forBlock['set_flag'] = function(block, generator) {
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    line_str.push(INDENT + INDENT + `L.LDPB(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   
    line_str.push(INDENT + LF); 

    return line_str.join("");
  };

  python.pythonGenerator.forBlock['set_output_during'] = function(block, generator) {
    //////////////////////////////////////////////////
    // 前処理
    //////////////////////////////////////////////////
    const out_pin_no = block.getFieldValue('output_list');
    const state = block.getFieldValue('state_list');
    const timer = block.getFieldValue('timer_list');
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    line_str.push(INDENT + INDENT + `L.LD(T, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   

    //////////////////////////////////////////////////
    // プロセス後動作
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
    line_str.push(INDENT + INDENT + `L.LDP(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `if (L.aax & L.iix):` + LF);
    if      (state === 'on')  line_str.push(INDENT + INDENT + INDENT + `RB.setOutputON(pin_no=${out_pin_no})` + LF); 
    else if (state === 'off') line_str.push(INDENT + INDENT + INDENT + `RB.setOutputOFF(pin_no=${out_pin_no})` + LF); 
    line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.TIM(T, ${block_addr.start_addr}, wait_msec=${timer})` + LF);
    line_str.push(INDENT + LF);

    return line_str.join("");
  };

  python.pythonGenerator.forBlock['set_output_wait'] = function(block, generator) {
    //////////////////////////////////////////////////
    // 前処理
    //////////////////////////////////////////////////
    const out_pin_no = block.getFieldValue('output_list');
    const out_state = block.getFieldValue('out_state_list');
    const in_pin_no = block.getFieldValue('input_list');
    const in_state = block.getFieldValue('in_state_list');
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    if      (in_state === 'none')  line_str.push(INDENT + INDENT + `L.LD(True)` + LF); 
    else if (in_state === 'on')    line_str.push(INDENT + INDENT + `L.LD(True if (RB.getBytesBase(input_port, target=${in_pin_no}, length=1) == 1) else False)` + LF); 
    else if (in_state === 'off')   line_str.push(INDENT + INDENT + `L.LD(True if (RB.getBytesBase(input_port, target=${in_pin_no}, length=1) == 0) else False)` + LF);     
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   

    //////////////////////////////////////////////////
    // プロセス後動作
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
    line_str.push(INDENT + INDENT + `L.LDP(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `if (L.aax & L.iix):` + LF);
    if      (out_state === 'on')  line_str.push(INDENT + INDENT + INDENT + `RB.setOutputON(pin_no=${out_pin_no})` + LF); 
    else if (out_state === 'off') line_str.push(INDENT + INDENT + INDENT + `RB.setOutputOFF(pin_no=${out_pin_no})` + LF); 
    line_str.push(INDENT + LF);

    return line_str.join("");
  };

  python.pythonGenerator.forBlock['wait_input'] = function(block, generator) {
    //////////////////////////////////////////////////
    // 前処理
    //////////////////////////////////////////////////
    const in_pin_no = block.getFieldValue('input_list');
    const in_state = block.getFieldValue('in_state_list');
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    if      (in_state === 'none')  line_str.push(INDENT + INDENT + `L.LD(True)` + LF); 
    else if (in_state === 'on')    line_str.push(INDENT + INDENT + `L.LD(True if (RB.getBytesBase(input_port, target=${in_pin_no}, length=1) == 1) else False)` + LF); 
    else if (in_state === 'off')   line_str.push(INDENT + INDENT + `L.LD(True if (RB.getBytesBase(input_port, target=${in_pin_no}, length=1) == 0) else False)` + LF);     
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   
    line_str.push(INDENT + LF);

    return line_str.join("");
  };

  python.pythonGenerator.forBlock['set_pallet'] = function(block, generator) {
    //////////////////////////////////////////////////
    // 前処理
    //////////////////////////////////////////////////
    let pallet_no = block.getFieldValue('no_list');
    let pallet_row = block.getFieldValue('row_list');
    let pallet_col = block.getFieldValue('col_list');
    let point_A_name = block.getFieldValue('A_list');
    let point_B_name = block.getFieldValue('B_list');
    let point_C_name = block.getFieldValue('C_list');
    let point_D_name = block.getFieldValue('D_list');
    // オフセット量計算に必要なデータを、パレットブロックから取得
    let point_A = [];
    let point_A_name_str = String(point_A_name);
    point_A.x = BlockFlow.json_data[point_A_name_str]['x_pos'];
    point_A.y = BlockFlow.json_data[point_A_name_str]['y_pos'];
    point_A.z = BlockFlow.json_data[point_A_name_str]['z_pos'];
    let point_B = [];
    let point_B_name_str = String(point_B_name);
    point_B.x = BlockFlow.json_data[point_B_name_str]['x_pos'];
    point_B.y = BlockFlow.json_data[point_B_name_str]['y_pos'];
    point_B.z = BlockFlow.json_data[point_B_name_str]['z_pos'];
    let point_C = [];
    let point_C_name_str = String(point_C_name);
    point_C.x = BlockFlow.json_data[point_C_name_str]['x_pos'];
    point_C.y = BlockFlow.json_data[point_C_name_str]['y_pos'];
    point_C.z = BlockFlow.json_data[point_C_name_str]['z_pos'];
    let point_D = [];
    let point_D_name_str = String(point_D_name);
    point_D.x = BlockFlow.json_data[point_D_name_str]['x_pos'];
    point_D.y = BlockFlow.json_data[point_D_name_str]['y_pos'];
    point_D.z = BlockFlow.json_data[point_D_name_str]['z_pos'];
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    line_str.push(INDENT + INDENT + `L.LDPB(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   

    //////////////////////////////////////////////////
    // プロセス後動作
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
    line_str.push(INDENT + INDENT + `L.LDP(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `if (L.aax & L.iix):` + LF);
    line_str.push(INDENT + INDENT + INDENT + `contents = {}` + LF);
    line_str.push(INDENT + INDENT + INDENT + `contents['cnt'] = 1` + LF);
    line_str.push(INDENT + INDENT + INDENT + `contents['row'] = ${pallet_row}` + LF);
    line_str.push(INDENT + INDENT + INDENT + `contents['col'] = ${pallet_col}` + LF);
    line_str.push(INDENT + INDENT + INDENT + `contents['A'] = {'x':${point_A.x}, 'y':${point_A.y}, 'z':${point_A.z}}` + LF);
    line_str.push(INDENT + INDENT + INDENT + `contents['B'] = {'x':${point_B.x}, 'y':${point_B.y}, 'z':${point_B.z}}` + LF);
    line_str.push(INDENT + INDENT + INDENT + `contents['C'] = {'x':${point_C.x}, 'y':${point_C.y}, 'z':${point_C.z}}` + LF);
    line_str.push(INDENT + INDENT + INDENT + `contents['D'] = {'x':${point_D.x}, 'y':${point_D.y}, 'z':${point_D.z}}` + LF);
    line_str.push(INDENT + INDENT + INDENT + `pallet_settings[${pallet_no}-1] = contents.copy()` + LF);
    line_str.push(INDENT + LF);

    return line_str.join("");
  };

  python.pythonGenerator.forBlock['move_next_pallet'] = function(block, generator) {
    //////////////////////////////////////////////////
    // 前処理
    //////////////////////////////////////////////////
    let pallet_no = block.getFieldValue('no_list');
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    line_str.push(INDENT + INDENT + `L.LDPB(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   

    //////////////////////////////////////////////////
    // プロセス後動作
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
    line_str.push(INDENT + INDENT + `L.LDP(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `if (L.aax & L.iix):` + LF);
    line_str.push(INDENT + INDENT + INDENT + `MAX_row = pallet_settings[${pallet_no}-1]['row']` + LF);
    line_str.push(INDENT + INDENT + INDENT + `MAX_col = pallet_settings[${pallet_no}-1]['col']` + LF);
    line_str.push(INDENT + INDENT + INDENT + `dst_pocket = pallet_settings[${pallet_no}-1]['cnt']` + LF);
    line_str.push(INDENT + INDENT + INDENT + `if ((dst_pocket <= MAX_row * MAX_col) and (dst_pocket > 0)):` + LF);
    line_str.push(INDENT + INDENT + INDENT + INDENT + `pallet_settings[${pallet_no}-1]['cnt'] = pallet_settings[${pallet_no}-1]['cnt'] + 1` + LF);
    line_str.push(INDENT + INDENT + INDENT + INDENT + `pallet_offset[${pallet_no}-1] = getPalletOffset(pallet, ${pallet_no})` + LF);
    line_str.push(INDENT + LF);

    return line_str.join("");
  };

  python.pythonGenerator.forBlock['reset_pallet'] = function(block, generator) {
    //////////////////////////////////////////////////
    // 前処理
    //////////////////////////////////////////////////
    let pallet_no = block.getFieldValue('no_list');
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    line_str.push(INDENT + INDENT + `L.LDPB(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   

    //////////////////////////////////////////////////
    // プロセス後動作
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
    line_str.push(INDENT + INDENT + `L.LDP(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `if (L.aax & L.iix):` + LF);
    line_str.push(INDENT + INDENT + INDENT + `pallet_settings[${pallet_no}-1]['cnt'] = 1` + LF);
    line_str.push(INDENT + INDENT + INDENT + `offset = {'x': 0.0, 'y': 0.0, 'z': 0.0}` + LF);
    line_str.push(INDENT + LF);

    return line_str.join("");
  };

  python.pythonGenerator.forBlock['controls_if'] = function(block, generator) {
    //////////////////////////////////////////////////
    // 前処理
    //////////////////////////////////////////////////  
    // 当該ブロックに接続されたインプットリストを取得
    let input_list = block.inputList;
    let if_condition = []
    for (let k = 0; k < input_list.length; k++) {
      let contents = []
      let input = input_list[k];
      // if入力条件の場合
      if(input.name.includes('IF')){
        // インプットから接続されたブロックを取得
        let input_block = input.connection.targetBlock();
        if (input_block && input_block.type === 'check_pallet') {
          let pallet_no = input_block.getFieldValue('no_list');
          let equation = input_block.getFieldValue('equation_list');
          let cnt = input_block.getFieldValue('cnt_list');
          contents.pallet_no = pallet_no;
          contents.name = input.name;
          contents.equation = equation;
          contents.cnt = cnt;
          if_condition.push(contents);
        }
      }
      else if(input.name === 'ELSE'){
        contents.pallet_no = null;
        contents.name = 'ELSE';
        contents.equation = null;
        contents.cnt = null;
        if_condition.push(contents);  
      }
    }

    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 

    //////////////////////////////////////////////////
    // プロセス前動作
    ////////////////////////////////////////////////// 
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Pre-Process:` + block.customId + LF);
    // check_palletブロックが条件式にあれば
    for (let i = 0; i < if_condition.length; i++) {
      let pallet_no = if_condition[i].pallet_no;
      let name = if_condition[i].name;
      let equation = if_condition[i].equation;
      let cnt;
      if (if_condition[i].cnt === 'max') cnt = `pallet_settings[${pallet_no}-1]['row']*pallet_settings[${pallet_no}-1]['col']`;
      else cnt = if_condition[i].cnt;
      // 条件式生成
      if(equation === '='){
        line_str.push(INDENT + INDENT + `try:` + LF);
        line_str.push(INDENT + INDENT + INDENT + `L.LDEQ(pallet_settings[${pallet_no}-1]['cnt'], ${cnt}+1)` + LF);
        line_str.push(INDENT + INDENT + INDENT + `${name} = L.OUTVAR()` + LF);
      }
      else if(equation === '>='){
        line_str.push(INDENT + INDENT + `try:` + LF);
        line_str.push(INDENT + INDENT + INDENT + `L.LDGEQ(pallet_settings[${pallet_no}-1]['cnt'], ${cnt}+1)` + LF);
        line_str.push(INDENT + INDENT + INDENT + `${name} = L.OUTVAR()` + LF);
      }
      else if(equation === '<='){
        line_str.push(INDENT + INDENT + `try:` + LF);
        line_str.push(INDENT + INDENT + INDENT + `L.LDLEQ(pallet_settings[${pallet_no}-1]['cnt'], ${cnt}+1)` + LF);
        line_str.push(INDENT + INDENT + INDENT + `${name} = L.OUTVAR()` + LF);
      }
      else if(equation === '>'){
        line_str.push(INDENT + INDENT + `try:` + LF);
        line_str.push(INDENT + INDENT + INDENT + `L.LDG(pallet_settings[${pallet_no}-1]['cnt'], ${cnt}+1)` + LF);
        line_str.push(INDENT + INDENT + INDENT + `${name} = L.OUTVAR()` + LF);
      }  
      else if(equation === '<'){
        line_str.push(INDENT + INDENT + `try:` + LF);
        line_str.push(INDENT + INDENT + INDENT + `L.LDL(pallet_settings[${pallet_no}-1]['cnt'], ${cnt}+1)` + LF);
        line_str.push(INDENT + INDENT + INDENT + `${name} = L.OUTVAR()` + LF);
      }  
      
      if(name === 'IF0')      line_str.push(INDENT + INDENT + `except KeyError: ${name} = False` + LF);
      else if(name === 'IF1') line_str.push(INDENT + INDENT + `except KeyError: ${name} = False` + LF);
      else if(name === 'IF2') line_str.push(INDENT + INDENT + `except KeyError: ${name} = False` + LF);
      else if(name === 'ELSE'){
        if(if_condition.length-1 >= 1) line_str.push(INDENT + INDENT + `L.LDB(IF0)` + LF);
        if(if_condition.length-1 >= 2) line_str.push(INDENT + INDENT + `L.ANB(IF1)` + LF);
        if(if_condition.length-1 >= 3) line_str.push(INDENT + INDENT + `L.ANB(IF2)` + LF);
        line_str.push(INDENT + INDENT + `${name} = L.OUTVAR()` + LF);
      }                    
    }
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    // 条件分岐2つ
    if (block_addr.stop3_addr){
      line_str.push(INDENT + INDENT + `L.LDB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop2_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop3_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.MRD()` + LF);
      line_str.push(INDENT + INDENT + `L.LD(IF0)` + LF);
      line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop2_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop3_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   
      line_str.push(INDENT + INDENT + `L.MRD()` + LF);
      line_str.push(INDENT + INDENT + `L.LD(IF1)` + LF);
      line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop2_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop3_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop2_addr})` + LF);   
      line_str.push(INDENT + INDENT + `L.MPP()` + LF);
      line_str.push(INDENT + INDENT + `L.LD(ELSE)` + LF);
      line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop3_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop2_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop3_addr})` + LF);   
    }
    // 条件分岐1つ
    else if (block_addr.stop2_addr){
      line_str.push(INDENT + INDENT + `L.LDB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop2_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.MRD()` + LF);
      line_str.push(INDENT + INDENT + `L.LD(IF0)` + LF);
      line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop2_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   
      line_str.push(INDENT + INDENT + `L.MPP()` + LF);
      line_str.push(INDENT + INDENT + `L.LD(ELSE)` + LF);
      line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop2_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop2_addr})` + LF);   
    }
    // 条件分岐無し
    else {
      line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.MPP()` + LF);
      line_str.push(INDENT + INDENT + `L.LD(IF0)` + LF);
      line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
      line_str.push(INDENT + INDENT + `L.ANL()` + LF);
      line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   
    }


    //////////////////////////////////////////////////
    // プロセス後動作
    //////////////////////////////////////////////////
    // line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
    // line_str.push(INDENT + INDENT + `L.LDP(${self.addr_str}, ${block_addr.start_addr})` + LF);
    // line_str.push(INDENT + INDENT + `if (L.aax & L.iix):` + LF);
    line_str.push(INDENT + LF);

    //ネストされたブロックの先頭空白を2つ分削除
    var condition = generator.statementToCode(block, 'CONDITION');
    var branches = ['DO0', 'DO1', 'ELSE'].map(label => generator.statementToCode(block, label)).join('\n');

    return line_str.join("") + branches.replace(/^ {2}/gm, ''); 
  };

  python.pythonGenerator.forBlock['check_pallet'] = function(block, generator) {
    // var dropdown_pallet_list = block.getFieldValue('no_list');
    // var dropdown_equation_list = block.getFieldValue('equation_list');
    // var dropdown_cnt_list = block.getFieldValue('cnt_list');
    return '';
  };

  python.pythonGenerator.forBlock['wait_during'] = function(block, generator) {
    //////////////////////////////////////////////////
    // 前処理
    //////////////////////////////////////////////////
    const timer = block.getFieldValue('timer_list');
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 
    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    line_str.push(INDENT + INDENT + `L.LD(T, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   

    //////////////////////////////////////////////////
    // プロセス後動作
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
    line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.TIM(T, ${block_addr.start_addr}, wait_msec=${timer})` + LF);
    line_str.push(INDENT + LF);

    return line_str.join("");
  };
  
  Blockly.Python['hand_pick'] = function(block) {
    //////////////////////////////////////////////////
    // 前処理
    //////////////////////////////////////////////////
    const hand_type = block.getFieldValue('hand_type_list');
    let in1_pin_no = '';
    let in1_state = '';
    let in2_pin_no = '';
    let in2_state = '';
    let out1_pin_no = '';
    let out1_state = '';
    let out2_pin_no = '';
    let out2_state = '';
    if(hand_type === 'single_SOL_suction'){
      in1_pin_no = '1';
      in1_state = 'on';
      in2_pin_no = '';
      in2_state = '';
      out1_pin_no = '1';
      out1_state = 'on';
      out2_pin_no = '';
      out2_state = '';
    }
    else if(hand_type === 'double_SOL_suction'){
      in1_pin_no = '1';
      in1_state = 'on';
      in2_pin_no = '';
      in2_state = '';
      out1_pin_no = '1';
      out1_state = 'on';
      out2_pin_no = '2';
      out2_state = 'off';
    }
    else if(hand_type === 'single_SOL_chuck'){
      in1_pin_no = '1';
      in1_state = 'off';
      in2_pin_no = '2';
      in2_state = 'off';
      out1_pin_no = '1';
      out1_state = 'on';
      out2_pin_no = '';
      out2_state = '';
    }
    else if(hand_type === 'double_SOL_chuck'){
      in1_pin_no = '1';
      in1_state = 'off';
      in2_pin_no = '2';
      in2_state = 'off';
      out1_pin_no = '1';
      out1_state = 'on';
      out2_pin_no = '2';
      out2_state = 'off';
    }
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 

    //////////////////////////////////////////////////
    // プロセス前動作
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Pre-Process:` + block.customId + LF);
    if (in1_state === 'on')       line_str.push(INDENT + INDENT + `L.LD(True if (RB.getBytesBase(input_port, target=${in1_pin_no}, length=1) == 1) else False)` + LF); 
    else if (in1_state === 'off') line_str.push(INDENT + INDENT + `L.LD(True if (RB.getBytesBase(input_port, target=${in1_pin_no}, length=1) == 0) else False)` + LF);
    if (in2_state === 'on')      line_str.push(INDENT + INDENT + `L.AND(True if (RB.getBytesBase(input_port, target=${in2_pin_no}, length=1) == 1) else False)` + LF); 
    else if (in2_state === 'off')  line_str.push(INDENT + INDENT + `L.AND(True if (RB.getBytesBase(input_port, target=${in2_pin_no}, length=1) == 0) else False)` + LF);
    else                          line_str.push(INDENT + INDENT + `L.AND(True)` + LF); 
    line_str.push(INDENT + INDENT + `if (L.aax & L.iix): sensor = True` + LF); 
    line_str.push(INDENT + INDENT + `else: sensor = False` + LF); 

    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    line_str.push(INDENT + INDENT + `L.LD(sensor)` + LF);        
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   

    //////////////////////////////////////////////////
    // プロセス後動作
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
    line_str.push(INDENT + INDENT + `L.LDP(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `if (L.aax & L.iix):` + LF);
    if      (out2_state === 'on')  line_str.push(INDENT + INDENT + INDENT + `RB.setOutputON(pin_no=${out2_pin_no})` + LF); 
    else if (out2_state === 'off') line_str.push(INDENT + INDENT + INDENT + `RB.setOutputOFF(pin_no=${out2_pin_no})` + LF); 
    if      (out1_state === 'on')  line_str.push(INDENT + INDENT + INDENT + `RB.setOutputON(pin_no=${out1_pin_no})` + LF); 
    else if (out1_state === 'off') line_str.push(INDENT + INDENT + INDENT + `RB.setOutputOFF(pin_no=${out1_pin_no})` + LF); 
    line_str.push(INDENT + LF);

    return line_str.join("");
  };

  Blockly.Python['hand_place'] = function(block) {
    //////////////////////////////////////////////////
    // 前処理
    //////////////////////////////////////////////////
    const hand_type = block.getFieldValue('hand_type_list');
    let in1_pin_no = '';
    let in1_state = '';
    let in2_pin_no = '';
    let in2_state = '';
    let out1_pin_no = '';
    let out1_state = '';
    let out2_pin_no = '';
    let out2_state = '';
    if(hand_type === 'single_SOL_suction'){
      in1_pin_no = '1';
      in1_state = 'on';
      in2_pin_no = '';
      in2_state = '';
      out1_pin_no = '';
      out1_state = '';
      out2_pin_no = '2';
      out2_state = 'on';
    }
    else if(hand_type === 'double_SOL_suction'){
      in1_pin_no = '1';
      in1_state = 'on';
      in2_pin_no = '';
      in2_state = '';
      out1_pin_no = '1';
      out1_state = 'off';
      out2_pin_no = '2';
      out2_state = 'on';
    }
    else if(hand_type === 'single_SOL_chuck'){
      in1_pin_no = '1';
      in1_state = 'on';
      in2_pin_no = '';
      in2_state = '';
      out1_pin_no = '';
      out1_state = '';
      out2_pin_no = '2';
      out2_state = 'on';
    }
    else if(hand_type === 'double_SOL_chuck'){
      in1_pin_no = '1';
      in1_state = 'on';
      in2_pin_no = '';
      in2_state = '';
      out1_pin_no = '1';
      out1_state = 'off';
      out2_pin_no = '2';
      out2_state = 'on';
    }
    //////////////////////////////////////////////////
    // アドレス参照
    //////////////////////////////////////////////////    
    const block_addr = self.getBlockAddr(block.customId); 

    //////////////////////////////////////////////////
    // プロセス前動作
    //////////////////////////////////////////////////
    let LF = '\n';
    let INDENT = '  ';
    let line_str = [];
    line_str.push(INDENT + INDENT + `#;Pre-Process:` + block.customId + LF);
    if (in1_state === 'on')      line_str.push(INDENT + INDENT + `L.LD(True if (RB.getBytesBase(input_port, target=${in1_pin_no}, length=1) == 1) else False)` + LF); 
    else if (in1_state === 'off')  line_str.push(INDENT + INDENT + `L.LD(True if (RB.getBytesBase(input_port, target=${in1_pin_no}, length=1) == 0) else False)` + LF);
    if (in2_state === 'on')      line_str.push(INDENT + INDENT + `L.AND(True if (RB.getBytesBase(input_port, target=${in2_pin_no}, length=1) == 1) else False)` + LF); 
    else if (in2_state === 'off')  line_str.push(INDENT + INDENT + `L.AND(True if (RB.getBytesBase(input_port, target=${in2_pin_no}, length=1) == 0) else False)` + LF);
    else                          line_str.push(INDENT + INDENT + `L.AND(True)` + LF); 
    line_str.push(INDENT + INDENT + `if (L.aax & L.iix): sensor = True` + LF); 
    line_str.push(INDENT + INDENT + `else: sensor = False` + LF); 

    //////////////////////////////////////////////////
    // プロセス
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Process:` + block.customId + LF);
    for (let i = 0; i < block_addr.onset1_addr_list.length; i++) {
      if(block_addr.onset1_addr_list[i] === 992002) line_str.push(INDENT + INDENT + `L.LD(CR, 2002)` + LF);
      else                               line_str.push(INDENT + INDENT + `L.LD(${self.addr_str}, ${block_addr.onset1_addr_list[i]})` + LF);
    }
    if(block_addr.reset_addr_list){
      for (let i = 0; i < block_addr.reset_addr_list.length; i++) line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.reset_addr_list[i]})` + LF);
    }
    line_str.push(INDENT + INDENT + `L.MPS()` + LF);
    line_str.push(INDENT + INDENT + `L.ANB(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.MPP()` + LF);
    line_str.push(INDENT + INDENT + `L.LD(sensor)` + LF);        
    line_str.push(INDENT + INDENT + `L.OR(${self.addr_str}, ${block_addr.stop1_addr})` + LF);
    line_str.push(INDENT + INDENT + `L.ANL()` + LF);
    line_str.push(INDENT + INDENT + `L.OUT(${self.addr_str}, ${block_addr.stop1_addr})` + LF);   

    //////////////////////////////////////////////////
    // プロセス後動作
    //////////////////////////////////////////////////
    line_str.push(INDENT + INDENT + `#;Post-Process:` + block.customId + LF);
    line_str.push(INDENT + INDENT + `L.LDP(${self.addr_str}, ${block_addr.start_addr})` + LF);
    line_str.push(INDENT + INDENT + `if (L.aax & L.iix):` + LF);
    if      (out1_state === 'on')  line_str.push(INDENT + INDENT + INDENT + `RB.setOutputON(pin_no=${out1_pin_no})` + LF); 
    else if (out1_state === 'off') line_str.push(INDENT + INDENT + INDENT + `RB.setOutputOFF(pin_no=${out1_pin_no})` + LF); 
    if      (out2_state === 'on')  line_str.push(INDENT + INDENT + INDENT + `RB.setOutputON(pin_no=${out2_pin_no})` + LF); 
    else if (out2_state === 'off') line_str.push(INDENT + INDENT + INDENT + `RB.setOutputOFF(pin_no=${out2_pin_no})` + LF); 
    line_str.push(INDENT + LF);

    return line_str.join("");
  };

  // python.pythonGenerator.forBlock['variables_set'] = function(block, generator) {
  // python.pythonGenerator.Python[''] = function(block) {
  //   // ブロックから変数名と値を取得
  //   var variableName = generator.nameDB_.getName(block.getFieldValue('VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  //   var value = generator.valueToCode(block, 'VALUE', generator.ORDER_NONE) || '0';
    
  //   // 変数の宣言部を生成
  //   var declarationCode = variableName + ' = (' + variableName + ' if isinstance(' + variableName + ', int) else 0)\n';
    
    
  //   // ブロックがループブロックに内包されている場合は、宣言部をループの外に移動する
  //   if (block.getParent().type == 'loop') {
  //     return declarationCode + variableName + ' += ' + value + '\n';
  //   } 
  //   else {
  //     console.log("ghogodhgodghodghd");

  //     return variableName + ' ++++++++= ' + value + '\n';
  //   }


  // };

  };
}