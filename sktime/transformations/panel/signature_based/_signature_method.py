"""Signature transformer."""

from sklearn.pipeline import Pipeline

from sktime.transformations.base import BaseTransformer
from sktime.transformations.panel.signature_based._augmentations import (
    _make_augmentation_pipeline,
)
from sktime.transformations.panel.signature_based._compute import (
    _WindowSignatureTransform,
)
from sktime.utils.validation._dependencies import _check_soft_dependencies


class SignatureTransformer(BaseTransformer):
    """Transformation class from the signature method.

    Follows the methodology laid out in the paper:
        "A Generalised Signature Method for Multivariate Time Series"

    Parameters
    ----------
    augmentation_list: Possible augmentation strings are
        ['leadlag', 'ir', 'addtime', 'cumsum', 'basepoint']
        default: ('basepoint', 'addtime')
    window_name: str, String from ['global', 'sliding', 'expanding', 'dyadic']
        default: 'dyadic'
    window_depth: int, The depth of the dyadic window. (Active only if
        `window_name == 'dyadic']`.
        default: 3
    window_length: int, The length of the sliding/expanding window. (Active
        only if `window_name in ['sliding, 'expanding'].
        default: None
    window_step: int, The step of the sliding/expanding window. (Active
        only if `window_name in ['sliding, 'expanding'].
        default: None
    rescaling: "pre" or "post",
                "pre": rescale the path last signature term should be roughly O(1)
                "post": Rescals the output signature by multiplying the depth-d term by d!.
                        Aim is that every term become ~O(1).
        default: None
    sig_tfm: One of: [‘signature’, ‘logsignature’]).
        default: 'signature'
    depth: int, Signature truncation depth.
        default: 4
    backend: str, The backend to use for signature computation. One of: 'esig', or 'iisignature'.
        default: 'esig'

    Attributes
    ----------
    signature_method: sklearn.Pipeline, A sklearn pipeline object that contains
        all the steps to extract the signature features.
    """

    _tags = {
        "scitype:transform-input": "Series",
        # what is the scitype of X: Series, or Panel
        "scitype:transform-output": "Primitives",
        # what is the scitype of y: None (not needed), Primitives, Series, Panel
        "scitype:instancewise": True,  # is this an instance-wise transform?
        "X_inner_mtype": "numpy3D",  # which mtypes do _fit/_predict support for X?
        "y_inner_mtype": "None",  # which mtypes do _fit/_predict support for X?#
        "fit_is_empty": False,
        "python_dependencies": "esig",
        "python_version": "<3.10",
    }

    def __init__(
        self,
        augmentation_list=("basepoint", "addtime"),
        window_name="dyadic",
        window_depth=3,
        window_length=None,
        window_step=None,
        rescaling=None,
        sig_tfm="signature",
        depth=4,
        backend="esig",
    ):
        if backend == "esig":
            _check_soft_dependencies("esig")
        elif backend == "iisignature":
            _check_soft_dependencies("iisignature")
        else:
            raise ValueError(
                "Error in SignatureTransformer, backend "
                "must be one of 'esig' or 'iisignature'"
            )

        self.augmentation_list = augmentation_list
        self.window_name = window_name
        self.window_depth = window_depth
        self.window_length = window_length
        self.window_step = window_step
        self.rescaling = rescaling
        self.sig_tfm = sig_tfm
        self.depth = depth
        self.backend = backend

        super().__init__()
        self.setup_feature_pipeline()

    def setup_feature_pipeline(self):
        """Set up the signature method as an sklearn pipeline."""
        augmentation_step = _make_augmentation_pipeline(self.augmentation_list)
        transform_step = _WindowSignatureTransform(
            window_name=self.window_name,
            window_depth=self.window_depth,
            window_length=self.window_length,
            window_step=self.window_step,
            sig_tfm=self.sig_tfm,
            sig_depth=self.depth,
            rescaling=self.rescaling,
            backend=self.backend,
        )

        # The so-called 'signature method' as defined in the reference paper
        self.signature_method = Pipeline(
            [
                ("augmentations", augmentation_step),
                ("window_and_transform", transform_step),
            ]
        )

    def _fit(self, X, y=None):
        self.signature_method.fit(X)
        return self

    def _transform(self, X, y=None):
        return self.signature_method.transform(X)

    @classmethod
    def get_test_params(cls, parameter_set="default"):
        """Return testing parameter settings for the estimator.

        Parameters
        ----------
        parameter_set : str, default="default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return `"default"` set.


        Returns
        -------
        params : dict or list of dict, default = {}
            Parameters to create testing instances of the class
            Each dict are parameters to construct an "interesting" test instance, i.e.,
            `MyClass(**params)` or `MyClass(**params[i])` creates a valid test instance.
            `create_test_instance` uses the first (or only) dictionary in `params`
        """
        params = {
            "augmentation_list": ("basepoint", "addtime"),
            "depth": 3,
            "window_name": "global",
        }
        return params
