from __future__ import division
from itertools import product

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

__alll__ = [
    "datasets_from_frame", "categorical_longform", "continuous_longform",
    "plot_categorical_diff", "plot_continuous_diff", "TrainTestDiff"
]


def _check_features_presence(datasets, features):
    for feature in features:
        for name, dataset in datasets.items():
            if feature not in dataset.columns:
                message = "`{}` feature missing in `{}`".format(feature, name)
                raise KeyError(message)


def datasets_from_frame(dataframe, feature):
    """Creates a dict dataset from a dataframe

    Given a categorical feature it creates a dict where each key is
    a level of the feature and each value is a dataframe, then you
    can use this datasets dict to plot graphs

    Args:
        dataframe (pandas.DataFrame): the frame that you're going to
            use to create a dict datasets
        feature (str): this feature will be used for grouping and
            creating the datasets dict

    Returns:
        datasets (dict)

    Raises:
        KeyError: if ``feature`` is not present in ``dataframe``
    """
    grouped = dataframe.groupby([feature])
    datasets = dict(e for e in grouped)

    return datasets


# Long Form Data


def _cat_longform(dataset, name, feature):
    data = dataset[feature].value_counts().reset_index()
    data.columns = ['level', 'count']
    data['feature'] = feature
    data['dataset'] = name
    data['prop'] = data['count'] / dataset.shape[0]

    return data


def _cont_longform(dataset, name, feature):
    data = pd.DataFrame()
    data['dataset'] = np.repeat(name, dataset.shape[0])
    data['feature'] = np.repeat(feature, dataset.shape[0])
    data['value'] = dataset[feature]

    return data


def _longform_frame(datasets, features, func):
    _check_features_presence(datasets, features)

    data_grid = product(datasets.items(), features)
    data = [func(d, n, f) for (n, d), f in data_grid]
    data = pd.concat(data)

    return data


def categorical_longform(datasets, features):
    """Given datasets and features it returns a long form representation of it

    Args:
        datasets (dict): each key is a dataset name and each value
            is a ``pandas.DataFrame``
        features (list): a list of string features present in the datasets

    Returns:
        longform (pd.DataFrame) A tidy longform dataframe with the following info:
            - dataset: a name of a dataset -key- present in ``datasets``
            - feature: a feature present in the ``features`` list
            - level: one of the different levels of feature
            - count: count the appearence of level in the dataset
            - prop: the proportion of level in the dataset

    Raises:
        KeyError: if any of the ``features`` isn't present in the ``datasets`` dict
    """
    longform = _longform_frame(datasets, features, _cat_longform)

    return longform


def continuous_longform(datasets, features):
    """Given datasets and features it returns a long form representation of it

    Args:
        datasets (dict): each key is a dataset name and each value is a ``pandas.DataFrame``
        features (list): a list of string features present in the datasets

    Returns:
        logform (pd.DataFrame): A tidy longform dataframe with the following info:
                - dataset: the name of one of the datasets present in ``datasets``
                - feature: feature name
                - value: the value of the feature in the current dataset

    Raises:
        KeyError: if any of the ``features`` isn't present in the ``datasets`` dict
    """
    longform = _longform_frame(datasets, features, _cont_longform)

    return longform


# Plot Style config

TITLE_FONTSIZE = 20
TITLE_YSPACE = 1.06


def plot_continuous_diff(datasets,
                         features,
                         kind="box",
                         col_wrap=3,
                         size=4,
                         aspect=1,
                         title=None):
    """Plots the distribution differences of continuous features in each dataset

    Args:
        datasets (dict):  a dict where the keys are names and the values
            are ``pandas.DataFrame``
        features (list): a list of continuous features present in every
            dataset of ``datasets``
        kind (str): {point, bar, box, violin, strip}
            The kind of plot to draw.
        col_wrap (int): how many charts you want per row
        size (float): Height (in inches)
        aspect (float): Aspect ratio of each facet, so that aspect * size gives the width
            of each facet in inches
        title (str): the title of the figure

    Returns:
        longform (pd.DataFrame): a long form (tidy) dataframe with the following
            columns:
                - dataset: the name of one of the datasets present in ``datasets``
                - feature: feature name
                - value: the value of the feature in the current dataset
        fig (matplotlib.Figure): a Matplotlib figure representing the differences
            of categorical ``features`` between ``datasets``

    Raises:
        KeyError: if any of the ``features`` isn't present in the ``datasets`` dict
    """
    if title is None:
        title = "{} differences".format("/".join(datasets.keys()))

    data = continuous_longform(datasets, features)
    grid = sns.factorplot(
        x="dataset",
        y="value",
        col="feature",
        data=data,
        kind=kind,
        sharey=False,
        size=size,
        aspect=aspect,
        col_wrap=col_wrap)

    grid.fig.suptitle(title, y=TITLE_YSPACE, fontsize=TITLE_FONTSIZE)

    return data, grid.fig


def plot_categorical_diff(datasets,
                          features,
                          kind="prop",
                          col_wrap=4,
                          size=4,
                          aspect=1,
                          title=None):
    """Plots the distribution differences of categorical features in each dataset

    Args:
        datasets (dict): a dict where the keys are names and the values
            are ``pandas.DataFrame``
        features (list): a list of categorical features present in every
            dataset of ``datasets``
        kind (Optional[str]): {count, prop}
            Use "count" for count of unique values for every level of a feature
            in every dataset present in ``datasets``
            Use "prop" for the proportion of that level of a feature
        col_wrap (int): how many charts you want per row
        size (float): Height (in inches)
        aspect (float): Aspect ratio of each facet, so that aspect * size gives the
            width of each facet in inches
        title (str): the title of the figure

    Returns:
        longform (pd.DataFrame): a long form (tidy) dataframe with the following
            columns:
                - dataset: a name of a dataset -key- present in ``datasets``
                - feature: a feature present in the ``features`` list
                - level: one of the different levels of feature
                - count: count the appearence of level in the dataset
                - prop: the proportion of level in the dataset
        fig (matplotlib.Figure): a Matplotlib figure representing the differences
            of categorical ``features`` between ``datasets``

    Raises:
        KeyError: if any of the ``features`` isn't present in the ``datasets`` dict
    """
    if title is None:
        title = "{} differences".format("/".join(datasets.keys()))

    longform_data = categorical_longform(datasets, features)

    # Group longform and sort by `features` order
    grouped_features = longform_data.groupby(['feature'])

    grouped_features = sorted(
        grouped_features, key=lambda x: features.index(x[0]))

    ncol = col_wrap
    n_axes = len(features)
    nrow = int(np.ceil(n_axes / col_wrap))

    figsize = (ncol * size * aspect, nrow * size)
    fig = plt.figure(figsize=figsize)
    fig.suptitle(title, y=TITLE_YSPACE, fontsize=TITLE_FONTSIZE)
    plt.subplots_adjust(wspace=0.5, hspace=0.35)

    axes = np.empty(n_axes, object)
    for i in range(n_axes):
        axes[i] = fig.add_subplot(nrow, ncol, i + 1)

    data_grid = zip(grouped_features, axes)
    for (name, data), ax in data_grid:
        sns.barplot(
            x="level", y=kind, hue="dataset", data=data, ax=ax).set_title(name)

    return longform_data, fig


class TrainTestDiff(object):
    """ Helper class to ease distribution analysis on the same datasets"""

    def __init__(self, datasets):
        self.datasets = datasets

    def plot_cont_diff(self,
                       features,
                       kind="box",
                       col_wrap=3,
                       size=4,
                       aspect=1,
                       title=None):
        """ See ``plot_continuous_diff`` documentation"""
        return plot_continuous_diff(self.datasets, features, kind, col_wrap,
                                    size, aspect, title)

    def plot_cat_diff(self, features, col_wrap=3, kind="prop", title=None):
        """ See ``plot_categorical_diff`` documentation"""
        return plot_categorical_diff(
            self.datasets, features, kind=kind, col_wrap=col_wrap, title=title)
