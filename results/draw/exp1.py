import matplotlib
import parse
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

from config import SAVE_FIG_FORMAT

# '60806040', contract deploy
# 'ed554eb8', fund
TX_SIG_KEYS = [
    'Latency-First Commit',
    'Latency-First Proof',
    'Regular',
]
TX_SIG = {
    'Regular': '620d4a67',
    'Latency-First Commit': '8d691c8b',
    'Latency-First Proof': '6b6f7f34',
}
TX_SIG_NAME = {y: x for x, y in TX_SIG.items()}
TX_SIG_FILENAME = {
    'Regular': 'online',
    'Latency-First Commit': 'commit',
    'Latency-First Proof': 'proof',
}

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

    # https://stackoverflow.com/a/39566040

    SMALL_SIZE = 18  # 8
    MEDIUM_SIZE = 24  # 10
    BIGGER_SIZE = 24  # 12

    plt.rc('font', size=SMALL_SIZE)  # controls default text sizes
    plt.rc('axes', titlesize=SMALL_SIZE)  # fontsize of the axes title
    plt.rc('axes', labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
    plt.rc('xtick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
    plt.rc('ytick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)  # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

    df = pd.read_excel('exp1.xlsx', engine='openpyxl')
    df = pd.DataFrame(df, columns=['filename', 'DataFirst4Byte', 'TransactionTime'])
    df['TransactionTime'] = df['TransactionTime'] / float(100000)  # ns -> ms

    filename_parser = parse.compile('exp-p{}-s{}')
    for i, row in df.iterrows():
        p, s = [int(x) for x in filename_parser.parse(row['filename'])]
        df.loc[i, 'PerformanceFactor'] = p
        df.loc[i, 'StateSizeFactor'] = s
    # https://www.statology.org/pandas-convert-column-to-int/
    df['PerformanceFactor'] = df['PerformanceFactor'].astype(int)
    df['StateSizeFactor'] = df['StateSizeFactor'].astype(int)
    for i, row in df.iterrows():
        sig = row['DataFirst4Byte']
        if sig in TX_SIG_NAME:
            df.loc[i, 'TransactionName'] = TX_SIG_NAME[sig]

    df_by_tx = {x: df[df['DataFirst4Byte'] == y] for x, y in TX_SIG.items()}

    df_by_state_size = {
        x: df[df['StateSizeFactor'] == x] for x in df['StateSizeFactor'].unique()
    }

    df = None
    del df

    assert sorted(TX_SIG.keys()) == sorted(TX_SIG_KEYS)
    for i, sig in enumerate(TX_SIG_KEYS):
        my_df = df_by_tx[sig]
        g = sns.catplot(
            kind="bar",
            data=my_df,
            x="PerformanceFactor", y="TransactionTime", hue='StateSizeFactor',
            errorbar="sd",
            palette="hls", alpha=1,
            height=4, aspect=1.8,
        )
        g.despine(left=True)
        g.set_axis_labels("Workload Factor", "CPU Time Cost (ms)")
        if i == len(TX_SIG_KEYS) - 1:
            g.legend.set_title("IO Factor")
            sns.move_legend(g, "center right", bbox_to_anchor=(0.95, 0.5), ncol=1)
            g.legend.set_frame_on(True)
        else:
            g.legend.remove()
        plt.savefig('output/fig-exp-1-{}.{}'.format(TX_SIG_FILENAME[sig], SAVE_FIG_FORMAT), bbox_inches='tight')

    for state_size, my_df in df_by_state_size.items():
        g = sns.catplot(
            kind="bar",
            data=my_df,
            x="PerformanceFactor", y="TransactionTime", hue='TransactionName',
            errorbar="sd",
            palette="hls", alpha=1,
            height=4, aspect=1.8,
        )
        g.despine(left=True)
        g.set_axis_labels("Workload Factor", "CPU Time Cost (ms)")
        g.legend.set_title("Transaction")
        g.legend.set_frame_on(True)
        sns.move_legend(g, "upper left", bbox_to_anchor=(0.125, 0.95))
        plt.savefig('output/fig-exp-1-s{}.{}'.format(int(state_size), SAVE_FIG_FORMAT), bbox_inches='tight')
