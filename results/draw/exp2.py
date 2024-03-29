import pathlib

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas
import pandas as pd
import matplotlib
from matplotlib.ticker import PercentFormatter, ScalarFormatter
import seaborn as sns

from config import SAVE_FIG_FORMAT

TX_SIG_NAME = {
    '620d4a67': 'Regular',
    '8d691c8b': 'Latency-First',
}
TX_SIG = {y: x for x, y in TX_SIG_NAME.items()}

CACHE_FILE = './cached-data.pkl'


def read_exp2(filename: str, gas: int, p: int) -> pd.DataFrame:
    df = pd.read_excel(filename, engine='openpyxl')
    df = pd.DataFrame(df, columns=['DataFirst4Byte', 'TransactionLatency'])
    df['TransactionLatency'] = df['TransactionLatency'] / float(1e9)  # ns -> s
    for i, row in df.iterrows():
        sig = row['DataFirst4Byte']
        df.loc[i, 'TransactionName'] = TX_SIG_NAME.get(sig, 'unknown')

    for i, _ in df.iterrows():
        df.loc[i, 'GasLimit'] = gas
        df.loc[i, 'PerformanceFactor'] = p
    df['GasLimit'] = df['GasLimit'].astype(int)
    df['PerformanceFactor'] = df['PerformanceFactor'].astype(int)

    return df[df['TransactionName'].isin(TX_SIG)]


if __name__ == '__main__':
    sns.set_style('whitegrid')
    if SAVE_FIG_FORMAT == 'pgf':
        # https://matplotlib.org/stable/tutorials/text/pgf.html
        matplotlib.use('pgf')
        plt.rcParams.update({
            "text.usetex": True,
            "pgf.texsystem": "pdflatex",
            "pgf.preamble": "\n".join([
                r"\usepackage[utf8x]{inputenc}",
                r"\usepackage[T1]{fontenc}",
                r"\usepackage{cmbright}",
            ]),
            "pgf.rcfonts": False,
            "font.serif": [],  # use latex default
            "font.sans-serif": [],  # use latex default
            "font.monospace": [],  # use latex default
            "font.family": "serif",
        })
    else:
        plt.rcParams.update({
            "text.usetex": False,
            "font.family": 'Times New Roman',
        })

    if pathlib.Path(CACHE_FILE).exists():
        print('Use cached data instead of loading the whole stuffs again.')
        df = pd.read_pickle(CACHE_FILE)
    else:
        df = pd.concat([read_exp2(filename, gas, p) for filename, gas, p in [
            ('exp2-online-p200-highgas.xlsx', 0x1ffffff, 200),
            ('exp2-online-p200-lowgas.xlsx', 0xffffff, 200),
            ('exp2-online-p500-highgas.xlsx', 0x1ffffff, 500),
            ('exp2-online-p500-lowgas.xlsx', 0xffffff, 500),
            ('exp2-p200-highgas.xlsx', 0x1ffffff, 200),
            ('exp2-p200-lowgas.xlsx', 0xffffff, 200),
            ('exp2-p500-highgas.xlsx', 0x1ffffff, 500),
            ('exp2-p500-lowgas.xlsx', 0xffffff, 500),
        ]], ignore_index=True)  # https://stackoverflow.com/a/46100235/7774607
        df.to_pickle(CACHE_FILE)

    # sns.catplot(data=df, x="PerformanceFactor", y="TransactionLatency", hue="GasLimit")
    df = df[df['TransactionName'].isin(TX_SIG)]
    g = sns.displot(
        data=df,
        x='TransactionLatency',
        hue=df['TransactionName'].astype(str)
            + ', Gas Limit = '
            + df['GasLimit'].astype(str)
            + ', Workload Factor = '
            + df['PerformanceFactor'].astype(str),
        # stat="density", common_norm=False, bins=30,
        # palette="cubehelix",
        alpha=1,
        height=3, aspect=2.8,  # multiple="dodge",
        kind='kde',
    )
    g.despine(top=False, right=False, left=False, bottom=False)
    g.set_axis_labels("Transaction Latency (s)")
    # https://seaborn.pydata.org/generated/seaborn.move_legend.html
    sns.move_legend(g, "upper center", bbox_to_anchor=(0.46, 0.95), framealpha=1.0)
    g.legend.set_title('')
    g.legend.set_frame_on(True)
    g.ax.set_xticks([5 * x for x in range(0, 10 + 1)])
    plt.savefig('output/fig-exp-2-kde-all.{}'.format(SAVE_FIG_FORMAT), bbox_inches='tight')
    # workaround: please manually do pdf cropping to this file

    df_groupby_gas = df.groupby('GasLimit')
    for gas in df_groupby_gas.groups.keys():
        df_groupby_gas_p = df_groupby_gas.get_group(gas).groupby('PerformanceFactor')
        for p in df_groupby_gas_p.groups.keys():
            my_df = df_groupby_gas_p.get_group(p)
            my_df = my_df[my_df['TransactionName'].isin(TX_SIG)]
            # g = sns.displot(
            #     data=my_df,
            #     x='TransactionLatency', hue='TransactionName',
            #     # stat="density", common_norm=False, bins=30,
            #     palette="dark", alpha=.6,
            #     height=2, aspect=1.8,  # multiple="dodge",
            #     kind='kde',
            # )
            # g.set_axis_labels("Transaction Latency (s)")
            # g.legend.set_title("Transaction")
            # sns.move_legend(g, "upper right", bbox_to_anchor=(0.675, 0.95))
            # g.legend.set_frame_on(True)
            # plt.savefig('output/fig-exp-2-kde-p{}-gas{}.{}'.format(int(p), int(gas), SAVE_FIG_FORMAT),
            #             bbox_inches='tight')

            g = sns.displot(
                data=my_df,
                x='TransactionLatency', hue='TransactionName',
                stat="proportion",  # 'count', 'density', 'percent', 'probability' or 'frequency'
                common_norm=False,
                # https://numpy.org/doc/stable/reference/generated/numpy.histogram_bin_edges.html#numpy.histogram_bin_edges
                bins=[float(x) for x in range(0, 30 + 1)],  # [float(0.5*x) for x in range(0, 60)],
                palette="cubehelix", alpha=0.1,
                height=2, aspect=2.8,
                kind='hist',
                multiple="layer",  # "layer", "stack", "fill", "dodge"
                element="step",  # "bars", "step", "poly"
                # fill=True,
                shrink=0.7,
                # rug=True,
            )
            g.despine(top=False, right=False, left=False, bottom=False)
            g.set_axis_labels("Transaction Latency (s)")
            g.legend.set_title("")
            sns.move_legend(g, "upper right", bbox_to_anchor=(0.78, 0.94), framealpha=1.0)
            g.legend.set_frame_on(True)
            g.ax.set_ylim(0, 1)
            g.ax.set_xticks([5 * x for x in range(0, 6 + 1)])
            g.tick_params()

            plt.savefig('output/fig-exp-2-hist-p{}-gas{}.{}'.format(int(p), int(gas), SAVE_FIG_FORMAT),
                        bbox_inches='tight')
