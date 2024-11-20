class MyBlocklyBlock {
  // クラス変数定義
  static setClassVariable(value) {
    MyBlocklyBlock.json_data = value;
  }
  constructor() {
    this.init_start_addr = 0;
    this.init_stop_addr  = 1000;
    this.addr_str = 'MR';
    this.ID   = 0;
    this.TYPE = 1;
    this.START_ADDR = 2;
    this.STOP_ADDR = 3;
    this.RESET_ADDR = 4;
    this.options = [
      ["Please update.", "P1"],
    ];
    this.for_block = [];

    Blockly.defineBlocksWithJsonArray([
        // startRobot
        {
          "type": "startrobot",
          "message0": "startRobot %1 %2 %3",
          "args0": [
            {
              "type": "input_dummy"
            },
            {
              "type": "field_dropdown",
              "name": "robot_name_list",
              "options": [
                [
                  "Dobot MG400",
                  "dobot_mg400"
                ],
                [
                  "IAI 3AXIS-TABLETOP",
                  "iai_3axis_tabletop"
                ],
                [
                  "IAI 4AXIS-TABLETOP",
                  "iai_4axis_tabletop"
                ],
                [
                  "YAMAHA SCARA",
                  "yamaha_scara"
                ]
              ]
            },
            {
              "type": "input_end_row"
            }
          ],
          "nextStatement": null,
          "colour": 230,
          "tooltip": "",
          "helpUrl": ""
        },
        // moveAbsLine
        {
          "type": "moveabsline",
          "message0": "moveAbsLine %1 %2 %3",
          "args0": [
            {
              "type": "input_dummy"
            },
            {
              "type": "field_dropdown",
              "name": "point_name_list",
              "options": this.options
            },
            {
              "type": "input_end_row"
            }
          ],
          "inputsInline": true,
          "previousStatement": null,
          "nextStatement": null,
          "colour": 270,
          "tooltip": "",
          "helpUrl": ""
        },
        // return
        {
          "type": "return",
          "message0": "return",
          "previousStatement": null,
          "colour": 270,
          "tooltip": "",
          "helpUrl": ""
        },
    ]);

    this.defineBlockGenerators();
  }

  // optionsを更新するメソッド
  updateOptions() {
    //////////////////////////////////////////////////
    // moveabslineの引数名を更新
    //////////////////////////////////////////////////
    this.options = []
    for (let key in MyBlocklyBlock.json_data) {
      this.options.push([MyBlocklyBlock.json_data[key]['name'], key]);
    }
    const local_wk = Blockly.getMainWorkspace();
    local_wk.getAllBlocks().forEach(block => {
      if (block.type === 'moveabsline') {
        const dropdownField = block.getField('point_name_list');
        if (dropdownField) {
          dropdownField.menuGenerator_ = this.options;
        }
      }
    });
    //////////////////////////////////////////////////
    // forブロック内のブロック達に関する情報を格納した2次元配列を生成
    //////////////////////////////////////////////////
    let all_blocks = local_wk.getAllBlocks();
    this.for_block = [];
    for (let i = 0; i < all_blocks.length; i++) {
      if ((all_blocks[i].type === 'controls_whileUntil') || (all_blocks[i].type === 'controls_if')) { // forループブロックを見つけた場合
        // forループ内のすべてのブロックを取得
        let do_input = all_blocks[i].getInput('DO'); //if は"DO0"
        if (do_input) {
          let target_block = do_input.connection.targetBlock();
          let block_cnt = 0;
          while (target_block !== null) {
            // forブロックに内包されているブロック情報を格納
            // リスト初期化
            let for_block_contents = [];
            // ID
            for_block_contents.push(target_block.id);
            // タイプ
            for_block_contents.push(target_block.type);
            if (target_block.type !== 'return'){
              // 開始アドレス
              let start_addr = Math.floor(block_cnt / 16) * 100 + (block_cnt % 16) + this.init_start_addr;
              for_block_contents.push(start_addr);
              // 完了アドレス
              let stop_addr = Math.floor(block_cnt / 16) * 100 + (block_cnt % 16) + this.init_stop_addr;
              for_block_contents.push(stop_addr);
            }
            else{
              // forブロック内に、returnブロック以外があれば
              if(block_cnt > 0){
                // 開始アドレス
                for_block_contents.push(-1);
                // 完了アドレス
                for_block_contents.push(-1);
                // リセットアドレス
                for_block_contents.push(this.for_block[block_cnt-1][this.STOP_ADDR]);
              }

            }
            block_cnt++;
            // 要素リストをまとめる
            this.for_block.push(for_block_contents);            
            // 次のブロックに進む
            target_block = target_block.getNextBlock();
          }
        }
      }
    }
    // console.log(this.for_block);
  }

  findElementPosition(array, element) {
    for (let i = 0; i < array.length; i++) {
      let subArray = array[i];
      let position = subArray.indexOf(element);
      if (position !== -1) {
        return [i, position]; // サブ配列のインデックスと要素の位置を返す
      }
    }
    return [-1, -1]; // 要素が見つからない場合は [-1, -1] を返す
  }

  defineBlockGenerators() {
    const self = this; // thisの値を安定化させる

    python.pythonGenerator.forBlock['startrobot'] = function(block, generator) {
      const robot_name = block.getFieldValue('robot_name_list');
      // let revised_robot_name = (robot_name.slice(1)).slice(0,-1); //文字列の最初と最後を除去
      let LF = '\n';
      let line_str = [];
      line_str.push('import importlib' + LF);
      line_str.push('import sys' + LF);
      line_str.push(LF);
      line_str.push("API_PATH = 'lib/robot/'" + LF);
      line_str.push('sys.path.append(self.current_dir + API_PATH)' + LF);
      line_str.push(`module = importlib.import_module(${robot_name}_api')` + LF);
      line_str.push('rb_api = module.RobotApi(robot_ip_address, robot_port, dev_port, baudrate)' + LF);

      return line_str.join("");
    };

      python.pythonGenerator.forBlock['moveabsline'] = function(block, generator) {      
      //////////////////////////////////////////////////
      // ブロック間のつながり情報を取得
      //////////////////////////////////////////////////
      let prev_stop_addr;
      let this_start_addr;
      let this_stop_addr;
      let this_reset_addr = [];
      let reset_info = {};
      if(self.for_block.length > 0){
        // 自身のブロックについて、二次元配列上の位置を取得
        let pos = self.findElementPosition(self.for_block, block.id);
        let for_block_index = pos[0];
        // ブロック情報取得
        // 前にブロックがあれば
        if(for_block_index > 0){
          // 前ブロックのアドレス
          prev_stop_addr = self.for_block[for_block_index-1][self.STOP_ADDR];
          // リセットアドレス
          reset_info.count = 0;
        }
        // 前にブロックが無ければ
        else{
          // 前ブロックのアドレス無し
          prev_stop_addr = -1;
          // リセットアドレス
          reset_info = self.for_block.reduce((accumulator, currentArray, rowIndex) => {
            let count = accumulator.count;
            let locations = accumulator.locations;
            currentArray.forEach((currentValue, colIndex) => {
              if (currentValue === 'return') {
                count++;
                locations.push({row: rowIndex, column: colIndex});
              }
            });
            return {count, locations};
          }, {count: 0, locations: []});
                   
          for (let i = 0; i < reset_info.count; i++) {
            this_reset_addr.push(self.for_block[reset_info.locations[i].row][self.RESET_ADDR]);
          }
        }
        // 自身
        this_start_addr = self.for_block[for_block_index][self.START_ADDR];
        this_stop_addr = self.for_block[for_block_index][self.STOP_ADDR];
      }

      //////////////////////////////////////////////////
      // シーケンス作成
      //////////////////////////////////////////////////
      const point_name = block.getFieldValue('point_name_list');
      let LF = '\n';
      let line_str = [];
      let point_name_str = String(point_name)
      let pos_x = MyBlocklyBlock.json_data[point_name_str]['x'];
      let pos_y = MyBlocklyBlock.json_data[point_name_str]['y'];
      let pos_z = MyBlocklyBlock.json_data[point_name_str]['z'];

      if(prev_stop_addr < 0) line_str.push(`b.LD(CR, 2002)` + LF);
      else                   line_str.push(`b.LD(${self.addr_str}, ${prev_stop_addr})` + LF);
      for (let i = 0; i < reset_info.count; i++) line_str.push(`b.ANB(${self.addr_str}, ${this_reset_addr[i]})` + LF);
      line_str.push(`b.MPS()` + LF);
      line_str.push(`b.ANB(${self.addr_str}, ${this_stop_addr})` + LF);
      line_str.push(`b.OUT(${self.addr_str}, ${this_start_addr})` + LF);
      line_str.push(`b.MPP()` + LF);
      line_str.push(`b.LD(CMP_move)` + LF);
      line_str.push(`b.ANPB(${self.addr_str}, ${this_start_addr})` + LF);
      line_str.push(`b.OR(${self.addr_str}, ${this_stop_addr})` + LF);
      line_str.push(`b.ANL()` + LF);
      line_str.push(`b.OUT(${self.addr_str}, ${this_stop_addr})` + LF);
      line_str.push(LF);

      // line_str.push(`rb_api.moveAbsoluteLine(x=${pos_x}, y=${pos_y}, z=${pos_z}, rx=0.0, ry=0.0, rz=0.0, vel=10.0, acc=10.0, dec=10.0)` + LF);    
    
      return line_str.join("");
      };

    python.pythonGenerator.forBlock['return'] = function(block, generator) {
      // TODO: Assemble python into code variable.
      var code = '';
      return code;
    };
  };
}