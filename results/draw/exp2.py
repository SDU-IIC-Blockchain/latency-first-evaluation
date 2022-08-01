import pathlib

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas
import pandas as pd
import matplotlib
from matplotlib.ticker import PercentFormatter, ScalarFormatter
import seaborn as sns

TX_SIG_NAME = {
    '620d4a67': 'Online (Original)',
    '8d691c8b': 'Commit',
}
TX_SIG = {y: x for x, y in TX_SIG_NAME.items()}

CACHE_FILE = './cached-data.pkl'

SAVE_FIG_FORMAT = 'pgf'


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
            + ', Performance Factor = '
            + df['PerformanceFactor'].astype(str),
        # stat="density", common_norm=False, bins=30,
        # palette="cubehelix",
        alpha=.6,
        height=3, aspect=2.8,  # multiple="dodge",
        kind='kde',
    )
    g.despine(left=True)
    g.set_axis_labels("Transaction Latency (s)")
    # https://seaborn.pydata.org/generated/seaborn.move_legend.html
    sns.move_legend(g, "upper center", bbox_to_anchor=(0.45, 0.95))
    g.legend.set_title('')
    g.legend.set_frame_on(True)
    plt.savefig('output/fig-exp-2-kde-all.{}'.format(SAVE_FIG_FORMAT), bbox_inches='tight')
    # workaround: please manually do pdf cropping to this file

    df_groupby_gas = df.groupby('GasLimit')
    for gas in df_groupby_gas.groups.keys():
        df_groupby_gas_p = df_groupby_gas.get_group(gas).groupby('PerformanceFactor')
        for p in df_groupby_gas_p.groups.keys():
            my_df = df_groupby_gas_p.get_group(p)
            my_df = my_df[my_df['TransactionName'].isin(TX_SIG)]
            g = sns.displot(
                data=my_df,
                x='TransactionLatency', hue='TransactionName',
                # stat="density", common_norm=False, bins=30,
                palette="dark", alpha=.6,
                height=2, aspect=1.8,  # multiple="dodge",
                kind='kde',
            )
            g.set_axis_labels("Transaction Latency (s)")
            g.legend.set_title("Transaction")
            sns.move_legend(g, "upper right", bbox_to_anchor=(0.675, 0.95))
            g.legend.set_frame_on(True)
            plt.savefig('output/fig-exp-2-kde-p{}-gas{}.{}'.format(int(p), int(gas), SAVE_FIG_FORMAT),
                        bbox_inches='tight')

            g = sns.displot(
                data=my_df,
                x='TransactionLatency', hue='TransactionName',
                stat="density", common_norm=False, bins=30,
                palette="cubehelix", alpha=.6,
                height=2, aspect=1.8,  # multiple="dodge",
                # kind='kde',
            )
            g.set_axis_labels("Transaction Latency (s)")
            g.legend.set_title("Transaction")
            sns.move_legend(g, "upper right", bbox_to_anchor=(0.675, 0.95))
            g.legend.set_frame_on(True)
            plt.savefig('output/fig-exp-2-hist-p{}-gas{}.{}'.format(int(p), int(gas), SAVE_FIG_FORMAT),
                        bbox_inches='tight')
