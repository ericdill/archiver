import os
import yaml
import logging
from channelarchiver import Archiver
from datetime import datetime

from _version import get_versions
__version__ = get_versions()['version']
del get_versions

logger = logging.getLogger(__name__)


def load_configuration(name, prefix, fields):
    """
    Load configuration data form a cascading series of locations.

    The precedence order is (highest priority last):

    1. CONDA_ENV/etc/{name}.yml (if CONDA_ETC_ env is defined)
    2. /etc/{name}.yml
    3. ~/.config/{name}/connection.yml
    4. reading {PREFIX}_{FIELD} environmental variables

    Parameters
    ----------
    name : str
        The expected base-name of the configuration files

    prefix : str
        The prefix when looking for environmental variables

    fields : iterable of strings
        The required configuration fields

    Returns
    ------
    conf : dict
        Dictionary keyed on ``fields`` with the values extracted
    """
    filenames = [os.path.join('/etc', name + '.yml'),
                 os.path.join(os.path.expanduser('~'), '.config',
                              name, 'connection.yml'),
                ]
    if 'CONDA_ETC_' in os.environ:
        filenames.insert(0, os.path.join(os.environ['CONDA_ETC_'],
                                         name + '.yml'))

    config = {}
    for filename in filenames:
        if os.path.isfile(filename):
            with open(filename) as f:
                config.update(yaml.load(f))
            logger.debug("Using archiver connection specified in config file. "
                         "\n%r", config)

    for field in fields:
        var_name = prefix + '_' + field.upper().replace(' ', '_')
        config[field] = os.environ.get(var_name, config.get(field, None))

    missing = [k for k, v in config.items() if v is None]
    if missing:
        raise KeyError("The configuration field(s) {0} were not found in any "
                       "file or environmental variable.".format(missing))
    return config

# connection_config = load_configuration('archiver', 'ARCH',
#                                        ['url', 'pv_dict'])
#
# # create a module level instance of the archiver
# archiver = Archiver(connection_config['url'])
# # scan the archiver on import to speed up data retrieval later
# archiver.scan_archives()
#
# # grab the pv dict from the connection config
# pv_dict = connection_config['pv_dict']


def get(pv, t0=None, t1=None, **kwargs):
    """Retrieve data for `pv` between `t0` and `t1` from the archiver

    Parameters
    ----------
    pv : str
        The alias to a pv that exists in the module_level pv_dict
        OR an actual PV.
    t0 : datetime, optional
        Start time to get data from the archiver.
        If None, defaults to t=0 in unix time
    t1 : datetime, optional
        End time to get data from the archiver
        If None, defaults to now
    **kwargs :
        keyword arguments for the Archiver.get function. See the Archiver.get
        docstring for verbose descriptions.
        Valid kwargs and their defaults in Archiver.get:
            limit=1000,
            interpolation='linear',
            scan_archives=True,
            archive_keys=None,
            tz=None

    Returns
    -------
    ChannelData : channelarchiver.models.ChannelData
    """
    valid_kwargs = ['limit', 'interpolation', 'scan_archives',
                    'archive_keys', 'tz']
    for kwarg in kwargs:
        if kwarg not in valid_kwargs:
            raise ValueError("%s is not a known kwarg to this function. Valid "
                             "kwargs = %s" % (kwarg, valid_kwargs))
    if t0 is None:
        t0 = datetime.fromtimestamp(0)
    if t1 is None:
        t1 = datetime.utcnow()
    pv_name = pv_dict.get(pv, pv)
    data = archiver.get(pv_name, t0, t1)
    return data


# function copied from data_muxer, need to rewrite
def add_pv(pv_lookup, pv_alias=None, upsample=None,
           downsample=None, **kwargs):
    """Add pv values from the archiver relevant for the times in this Muxer

    This function will determine the earliest (t0) and latest (t1) event
    times that are in this data muxer. It will then go to the archiver
    and get all data for the pv specified by pv_name or pv_alias

    Parameters
    ----------
    pv_lookup : str
        An EPICS PV or an alias (key in dataportal.archiver.pv_dict)
        If this parameter is an EPICS PV, it is recommended that you also
        provide a pv_alias.
    pv_alias : str, optional
        The alias for `pv_lookup`
    upsample : str or callable, optional
        See ColSpec.upsample for valid options
    downsample : str or callable, optional
        See ColSpec.downsample for valid options
    kwargs :
        keyword arguments to `Archiver.get()`. See
        `dataportal.archiver.get()` or `channelarchiver.Archiver.get()`
        for valid kwargs
    """
    if ':' in pv_lookup:
        # At NSLS-II, all PVs have a colon in the name.
        for k, v in six.iteritems(archiver.pv_dict):
            if pv_lookup == v:
                pv_alias = k
        if pv_alias is None:
            pv_alias = pv_lookup
    else:
        # If there is no colon, then pv_name is actually the pv_alias. See
        # if we know about this alias from archiver.yml
        if pv_alias is None:
            pv_alias = pv_lookup
        pv_lookup = archiver.pv_dict[pv_alias]

    # grab all event times
    times = [v for dct in self._time for v in six.itervalues(dct)]
    # turn the earliest and latest timestamps into datetime objects
    # because that is what channelarchiver expects
    t0 = datetime.fromtimestamp(np.min(times))
    t1 = datetime.fromtimestamp(np.max(times))
    # get the data from the archiver
    data = archiver.get(pv_lookup, t0, t1, **kwargs)
    # add the archiver data to the data list
    for val in data.values:
        self._data.append({pv_lookup: val})
    # add thd archiver timestamps
    for dt in data.times:
        timestamp = ttime.mktime(dt.timetuple())
        self._time.append(timestamp)
        # @danielballan; it is necessary to append the archiver data to
        # the timestamps list?
        self._timestamps.append({pv_lookup: timestamp})
    # add the pv info to the list of known sources
    self.sources[pv_alias] = pv_lookup
    if upsample is None:
        upsample = self.default_upsample
    if downsample is None:
        downsample = self.default_downsample
    # create a ColSpec and add keep track of it in col_info
    col_info = ColSpec(pv_alias, 0, [], upsample, downsample)
    self.col_info[pv_alias] = col_info
