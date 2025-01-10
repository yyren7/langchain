from typing import Any, Tuple, Optional
from transitions import Machine
from transitions.extensions import GraphMachine
import pandas as pd
import logging

# 状態遷移を司るステートマシン
# transitionライブラリで作るステートマシンは非常に多機能で、同じ動作でも複数のコーディング方法があったり
# transitionの仕様の把握が必要な暗黙的な処理が多いので、作り込むと複雑すぎてメンテも大変だし可読性も下がる。
# このライブラリはシンプルに状態遷移の機能と作成したステートマシンの図示や挙動確認だけを提供する。


class StateMachine(object):
    def __init__(self, transition_csv: str = '',
                 initial_state: str = 'BOOT',
                 use_graph: bool = False,
                 show_transition: bool = True,
                 logger_id: str = ""):
        """ StateMachineの引数は以下
        transition_csv:先述の遷移を記述したcsv
        initial_state:状態遷移の初期状態(string型)
        use_graph:図示系の機能を使用するかどうか。使うと動作が遅くなるらしいので、デバッグ用に。
                動作にはgraphvizのセットアップが必要。詳細は元リポジトリで
                https://github.com/pytransitions/transitions
        show_transition:実行した遷移をprint表示するかどうか
        """
        # オプションを処理
        self.logger = logging.getLogger(logger_id)
        self.USE_GRAPH = use_graph
        if show_transition:
            before_state_change = '_action_before_state_change'
            after_state_change = '_action_after_state_change'
        else:
            before_state_change = "_action_before_state_change"
            after_state_change = None  # type:ignore
        # csvファイルから状態遷移を生成
        self.transitions = []  # type:ignore
        self.df_transition = pd.read_csv(transition_csv)
        # /で始まる行はコメントとして無視。
        for index, item in self.df_transition.iterrows():
            if item["Source"][0] == "/":
                self.df_transition = self.df_transition.drop(index=index)  # type:ignore
        self._define_transitions()
        self.initial_state = initial_state
        # ステートマシンを作成
        if self.USE_GRAPH:
            self.machine = GraphMachine(model=self,
                                        states=self.states,
                                        initial=self.initial_state,
                                        transitions=self.transitions,
                                        auto_transitions=False,  # NOTE:これがないと勝手に全状態への遷移命令が作られる
                                        before_state_change=before_state_change,
                                        after_state_change=after_state_change,
                                        send_event=True,
                                        queued=True)
        else:
            self.machine = Machine(model=self,  # type:ignore
                                   states=self.states,
                                   initial=self.initial_state,
                                   transitions=self.transitions,
                                   auto_transitions=False,
                                   send_event=True,
                                   before_state_change=before_state_change,
                                   after_state_change=after_state_change,
                                   queued=True)
        self.event_buf = None

    def _action_before_state_change(self, event) -> None:
        # 常に実行される。
        # 状態遷移前に実行されるメソッド。遷移の情報を記録する。
        self.event_buf = event

    def _action_after_state_change(self, event) -> None:
        # show_transitionオプション時
        # 状態遷移後に実行されるメソッド。
        # print('%s : %s => %s' % (event.event.name, event.transition.source, self.state))
        self.logger.debug('%s : %s => %s' % (
            event.event.name, event.transition.source, self.state))  # type: ignore

    def _define_transitions(self) -> None:
        # csvファイルから状態遷移を生成。何も複雑なことはない。
        self.transitions = []
        self.states = []
        for index, item in self.df_transition.iterrows():
            source = item["Source"]
            dest = item["Destination"]
            self.transitions.append({'trigger': item["Trigger"],
                                     'source': source,
                                     'dest': dest})
            self.states.append(source)
            self.states.append(dest)
        # 定義された状態遷移から、重複のない状態リストを作成。ステートマシンに登録するため。
        self.states = list(set(self.states))

    def get_state_transition_graph(self) -> Any:
        # USE_GRAPHオプション使用時
        # 状態遷移図をgraphvizのDigraphクラスで返す。
        if self.USE_GRAPH:
            return self.get_graph()  # type:ignore
        else:
            # print("use graph option is off")
            pass
            return None

    def save_state_transition_pngimg(self, output_filename) -> Any:
        # USE_GRAPHオプション使用時
        # 状態遷移図をpng形式で保存する。
        if self.USE_GRAPH:
            graph = self.get_graph()  # type:ignore
            graph.attr('graph', rankdir="LR", layout="dot")
            graph.format = "png"
            graph.render(output_filename)
            # return graph.render(output_filename)
        else:
            # print("use graph option is off")
            pass
            return None

    def view_state_transition(self) -> Any:
        # USE_GRAPHオプション使用時
        # 状態遷移図をodfで見る。
        if self.USE_GRAPH:
            return self.get_graph().view()  # type:ignore
        else:
            # print("use graph option is off")
            pass
            return None

    def is_valid_transition(self, trig) -> bool:
        # 未定義の状態遷移を命令すると例外が出てしまう。
        # 間違った状態遷移を指示した後も、止めずに処理を継続するには
        # 事前確認が必要。
        is_valid = False
        for t in self.transitions:
            if trig == t["trigger"]:
                source = t["source"]
                # print(len(source))
                if isinstance(source, str):
                    if self.state == source:  # type:ignore
                        is_valid = True
                else:
                    if self.state in source:  # type:ignore
                        is_valid = True
        return is_valid

    def get_previous_transition(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        # 直前に実行された遷移の情報(トリガー名、遷移元、遷移先)を返す。
        if self.event_buf is not None:
            source = self.event_buf.transition.source
            dest = self.event_buf.transition.dest
            trigger = self.event_buf.event.name
            return trigger, source, dest
        else:
            return None, None, None

    # ===============================================================================
    # NOTE: 以下aoyama追記
    # ===============================================================================

    def current_state(self) -> str:
        return self.state  # type:ignore

    def transition(self, trig: str):
        try:
            self.trigger(trig)  # type:ignore
            trigger, source, dest = self.get_previous_transition()
            print(trigger, source, dest)
        except Exception:
            pass


if __name__ == "__main__":
    transition_csv = r"./transition_demo.csv"
    stmach = StateMachine(transition_csv=transition_csv, initial_state="BOOT",
                          use_graph=False, show_transition=False)
    # ステートマシンで定義した状態遷移を図示
    stmach.view_state_transition()

    # 状態の遷移はステートマシンのtriggerで実行する。
    # 引数に実行したい遷移のトリガー名を入れる。
    stmach.transition("TO_IDLING")  # TO_IDLINGトリガーで定義された状態遷移を実行
    stmach.transition("TO_INSPECT")  # TO_INSPECTトリガーで定義された状態遷移を実行
    stmach.transition("EXCEPTION")  # EXCEPTIONトリガーで定義された状態遷移を実行
    stmach.transition("RESET")  # RESETトリガーで定義された状態遷移を実行
    # 上記はBOOT => IDLING => INSPECTION => ERROR => BOOTの遷移になる。
