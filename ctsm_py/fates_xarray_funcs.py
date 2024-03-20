'''functions for using fates and xarray'''
import xarray as xr
import numpy as np

def _get_check_dim(dim_short, dataset):
    """Get dim name from short code and ensure it's on Dataset
    
    Probably only useful internally to this module; see deduplex().

    Args:
        dim_short (string): The short name of the dimension. E.g., "age"
        dataset (xarray Dataset): The Dataset we expect to include the dimension

    Raises:
        NameError: Dimension not found on Dataset

    Returns:
        string: The long name of the dimension. E.g., "fates_levage"
    """
    
    dim = "fates_lev" + dim_short
    if dim not in dataset.dims:
        raise NameError(f"Dimension {dim} not present in Dataset with dims {dataset.dims}")
    return dim


def deduplex(dataset, this_var, dim1_short, dim2_short, preserve_order=True):
    """Reshape a duplexed FATES dimension into its constituent dimensions
    
    For example, given a variable with dimensions
        (time, fates_levagepft, lat, lon),
    this will return a DataArray with dimensions
        (time, fates_levage, fates_levpft, lat, lon)
    Or with reorder=False:
        (time, fates_levpft, lat, lon, fates_levage).

    Args:
        dataset (xarray Dataset): Dataset containing the variable with dimension to de-duplex
        this_var (string or xarray DataArray): (Name of) variable with dimension to de-duplex
        dim1_short (string): Short name of first duplexed dimension. E.g., when de-duplexing
                             fates_levagepft, dim1_short=age.
        dim2_short (string): Short name of second duplexed dimension. E.g., when de-duplexing
                             fates_levagepft, dim2_short=pft.
        preserve_order (bool, optional): Preserve order of dimensions of input DataArray? Defaults
                                         to True. Might be faster if False. See examples above.

    Raises:
        TypeError: Incorrect type of this_var
        NameError: Dimension not found on Dataset
    
    Returns:
        xarray DataArray: De-duplexed variable
    """

    # Get DataArray
    if isinstance(this_var, xr.DataArray):
        da_in = this_var
    elif isinstance(this_var, str):
        da_in = dataset[this_var]
    else:
        raise TypeError("this_var must be either string or DataArray, not " + type(this_var))

    # Get combined dim name
    dim_combined = "fates_lev" + dim1_short + dim2_short
    if dim_combined not in da_in.dims:
        raise NameError(f"Dimension {dim_combined} not present in DataArray with dims {da_in.dims}")

    # Get individual dim names
    dim1 = _get_check_dim(dim1_short, dataset)
    dim2 = _get_check_dim(dim2_short, dataset)

    # Split multiplexed dimension into its components
    n_dim1 = len(dataset[dim1])
    da_out = (da_in.rolling({dim_combined: n_dim1}, center=False)
            .construct(dim1)
            .isel({dim_combined: slice(n_dim1-1, None, n_dim1)})
            .rename({dim_combined: dim2})
            .assign_coords({dim1: dataset[dim1]})
            .assign_coords({dim2: dataset[dim2]}))

    # Reorder so that the split dimensions are together and in the expected order
    if preserve_order:
        new_dim_order = []
        for dim in da_out.dims:
            if dim == dim2:
                new_dim_order.append(dim1)
            if dim != dim1:
                new_dim_order.append(dim)
        da_out = da_out.transpose(*new_dim_order)

    return da_out


def agefuel_to_age_by_fuel(agefuel_var, dataset):
    """function to reshape a fates multiplexed age and fuel size indexed variable to one indexed by age and fuel size
    first argument should be an xarray DataArray that has the FATES AGEFUEL dimension
    second argument should be an xarray Dataset that has the FATES FUEL dimension 
    (possibly the dataset encompassing the dataarray being transformed)
    returns an Xarray DataArray with the size and pft dimensions disentangled"""
    n_age = len(dataset.fates_levage)
    ds_out = (agefuel_var.rolling(fates_levagefuel=n_age, center=False)
            .construct("fates_levage")
            .isel(fates_levagefuel=slice(n_age-1, None, n_age))
            .rename({'fates_levagefuel':'fates_levfuel'})
            .assign_coords({'fates_levage':dataset.fates_levage})
            .assign_coords({'fates_levfuel':dataset.fates_levfuel}))
    ds_out.attrs['long_name'] = agefuel_var.attrs['long_name']
    ds_out.attrs['units'] = agefuel_var.attrs['units']
    return(ds_out)

def scpf_to_scls_by_pft(scpf_var, dataset):
    """function to reshape a fates multiplexed size and pft-indexed variable to one indexed by size class and pft
    first argument should be an xarray DataArray that has the FATES SCPF dimension
    second argument should be an xarray Dataset that has the FATES SCLS dimension 
    (possibly the dataset encompassing the dataarray being transformed)
    returns an Xarray DataArray with the size and pft dimensions disentangled"""
    n_scls = len(dataset.fates_levscls)
    ds_out = (scpf_var.rolling(fates_levscpf=n_scls, center=False)
            .construct("fates_levscls")
            .isel(fates_levscpf=slice(n_scls-1, None, n_scls))
            .rename({'fates_levscpf':'fates_levpft'})
            .assign_coords({'fates_levscls':dataset.fates_levscls})
            .assign_coords({'fates_levpft':dataset.fates_levpft}))
    ds_out.attrs['long_name'] = scpf_var.attrs['long_name']
    ds_out.attrs['units'] = scpf_var.attrs['units']
    return(ds_out)


def scag_to_scls_by_age(scag_var, dataset):
    """function to reshape a fates multiplexed size and pft-indexed variable to one indexed by size class and pft                                                                                                      
    first argument should be an xarray DataArray that has the FATES SCAG dimension                                                                                                                                     
    second argument should be an xarray Dataset that has the FATES age dimension                                                                                                                                      
   (possibly the dataset encompassing the dataarray being transformed)                                                                                                                                                     returns an Xarray DataArray with the size and age dimensions disentangled"""
    n_scls = len(dataset.fates_levscls)
    ds_out = (scag_var.rolling(fates_levscag=n_scls, center=False)
            .construct("fates_levscls")
            .isel(fates_levscag=slice(n_scls-1, None, n_scls))
            .rename({'fates_levscag':'fates_levage'})
            .assign_coords({'fates_levscls':dataset.fates_levscls})
            .assign_coords({'fates_levage':dataset.fates_levage}))
    ds_out.attrs['long_name'] = scag_var.attrs['long_name']
    ds_out.attrs['units'] = scag_var.attrs['units']
    return(ds_out)



def monthly_to_annual(array):
    """ calculate annual mena from monthly data, using unequal month lengths fros noleap calendar.  
    originally written by Keith Lindsay."""
    mon_day  = xr.DataArray(np.array([31.,28.,31.,30.,31.,30.,31.,31.,30.,31.,30.,31.]), dims=['month'])
    mon_wgt  = mon_day/mon_day.sum()
    return (array.rolling(time=12, center=False) # rolling
            .construct("month") # construct the array
            .isel(time=slice(11, None, 12)) # slice so that the first element is [1..12], second is [13..24]
            .dot(mon_wgt, dims=["month"]))

def monthly_to_month_by_year(array):
    """ go from monthly data to month x year data (for calculating climatologies, etc"""
    return (array.rolling(time=12, center=False) # rolling
            .construct("month") # construct the array
            .isel(time=slice(11, None, 12)).rename({'time':'year'}))


