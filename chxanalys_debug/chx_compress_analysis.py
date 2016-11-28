

from __future__ import absolute_import, division, print_function

from tqdm import tqdm
import struct        

import matplotlib.pyplot as plt

from chxanalys.chx_libs import (np, roi, time, datetime, os,  getpass, db, get_images,LogNorm,Figure, RUN_GUI)
#from chxanalys.chx_generic_functions import (get_circular_average)
#from chxanalys.XPCS_SAXS import (get_circular_average)

import os
from chxanalys.chx_generic_functions import ( save_arrays )


from skbeam.core.utils import multi_tau_lags
from skbeam.core.roi import extract_label_indices
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

from chxanalys.chx_compress import   (compress_eigerdata, read_compressed_eigerdata,init_compress_eigerdata, 
                                      Multifile,pass_FD,get_avg_imgc,mean_intensityc, get_each_frame_intensityc)

                                      
#from chxanalys.chx_compress import *



def cal_waterfallc(FD, labeled_array,   qindex=1, save=False, *argv,**kwargs):   
    """Compute the mean intensity for each ROI in the compressed file (FD)

    Parameters
    ----------
    FD: Multifile class
        compressed file
    labeled_array : array
        labeled array; 0 is background.
        Each ROI is represented by a nonzero integer. It is not required that
        the ROI labels are contiguous
    qindex : int 
        The ROI's to use.  
    save: save the waterfall

    Returns
    -------
    waterfall : array
        The mean intensity of each ROI for all `images`
        Dimensions:
            len(mean_intensity) == len(index)
            len(mean_intensity[0]) == len(images)
    index : list
        The labels for each element of the `mean_intensity` list
    """
    sampling =1
    
    labeled_array_ = np.array( labeled_array == qindex, dtype= np.int64)
    
    qind, pixelist = roi.extract_label_indices(  labeled_array_  ) 
    
    if labeled_array_.shape != ( FD.md['ncols'],FD.md['nrows']):
        raise ValueError(
            " `image` shape (%d, %d) in FD is not equal to the labeled_array shape (%d, %d)" %( FD.md['ncols'],FD.md['nrows'], labeled_array_.shape[0], labeled_array_.shape[1]) )
          
    # pre-allocate an array for performance
    # might be able to use list comprehension to make this faster
    
    watf = np.zeros(   [ int( ( FD.end - FD.beg)/sampling ), len(qind)] )    
    
    #fra_pix = np.zeros_like( pixelist, dtype=np.float64)
    
    timg = np.zeros(    FD.md['ncols'] * FD.md['nrows']   , dtype=np.int32   ) 
    timg[pixelist] =   np.arange( 1, len(pixelist) + 1  ) 
    
    
    
    #maxqind = max(qind)    
    norm = np.bincount( qind  )[1:]
    n= 0         
    #for  i in tqdm(range( FD.beg , FD.end )):        
    for  i in tqdm(range( FD.beg, FD.end, sampling  ), desc= 'Get waterfall for q index=%s'%qindex ):
        (p,v) = FD.rdrawframe(i)
        w = np.where( timg[p] )[0]
        pxlist = timg[  p[w]   ] -1        
       
        watf[n][pxlist] =  v[w]
        n +=1   
    if save:
        path = kwargs['path'] 
        uid = kwargs['uid']
        np.save(  path + 'uid=%s--waterfall'%uid, watf) 
            
    return watf

def plot_waterfallc(wat, qindex=1, aspect = None,vmax=None, vmin=None,save=False, return_fig=False,*argv,**kwargs):   
    '''plot waterfall for a giving compressed file
    
       FD: class object, the compressed file handler
       labeled_array: np.array, a ROI mask
       qindex: the index number of q, will calculate where( labeled_array == qindex)
       aspect: the aspect ratio of the plot
       
       Return waterfall
       Plot the waterfall
    
    '''    
    #wat = cal_waterfallc( FD, labeled_array, qindex=qindex)
    if RUN_GUI:
        fig = Figure(figsize=(8,6))
        ax = fig.add_subplot(111)
    else:
        fig, ax = plt.subplots(figsize=(8,6))   
    #fig, ax = plt.subplots(figsize=(8,6))
    ax.set_ylabel('Pixel')
    ax.set_xlabel('Frame')
    ax.set_title('Waterfall_Plot_@qind=%s'%qindex)
    if 'beg' in kwargs:
        beg = kwargs['beg']
    else:
        beg=0
    
    extent = [  beg, len(wat)+beg, 0, len( wat.T) ]
    if vmax is None:
        vmax=wat.max()
    if vmin is None:
        vmin = wat.min()
    if aspect is None:
        aspect = wat.shape[0]/wat.shape[1]
    im = ax.imshow(wat.T, cmap='viridis', vmax=vmax,extent= extent)
    fig.colorbar( im   )
    ax.set_aspect( aspect)
    
    if save:
        #dt =datetime.now()
        #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)             
        path = kwargs['path'] 
        if 'uid' in kwargs:
            uid = kwargs['uid']
        else:
            uid = 'uid'
        #fp = path + "uid= %s--Waterfall-"%uid + CurTime + '.png'     
        fp = path + "uid=%s--Waterfall-"%uid  + '.png'    
        plt.savefig( fp, dpi=fig.dpi)
        
    #plt.show()
    if return_fig:
        return fig,ax, im 
    
    


def get_waterfallc(FD, labeled_array, qindex=1, aspect = 1.0,
                   vmax=None, save=False, *argv,**kwargs):   
    '''plot waterfall for a giving compressed file
    
       FD: class object, the compressed file handler
       labeled_array: np.array, a ROI mask
       qindex: the index number of q, will calculate where( labeled_array == qindex)
       aspect: the aspect ratio of the plot
       
       Return waterfall
       Plot the waterfall    
    '''
    
    wat = cal_waterfallc( FD, labeled_array, qindex=qindex)
    
    fig, ax = plt.subplots(figsize=(8,6))
    ax.set_ylabel('Pixel')
    ax.set_xlabel('Frame')
    ax.set_title('Waterfall_Plot_@qind=%s'%qindex)

    im = ax.imshow(wat.T, cmap='viridis', vmax=vmax)
    fig.colorbar( im   )
    ax.set_aspect( aspect)
    
    if save:
        #dt =datetime.now()
        #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)             
        path = kwargs['path'] 
        if 'uid' in kwargs:
            uid = kwargs['uid']
        else:
            uid = 'uid'
        #fp = path + "uid= %s--Waterfall-"%uid + CurTime + '.png'     
        fp = path + "uid=%s--Waterfall-"%uid  + '.png'    
        fig.savefig( fp, dpi=fig.dpi) 
        
    plt.show()
    return  wat







def get_each_ring_mean_intensityc( FD, ring_mask, sampling=1, timeperframe=None, plot_ = True , save=False, *argv,**kwargs):   
    
    """
    get time dependent mean intensity of each ring
    """
    
    mean_int_sets, index_list = mean_intensityc(FD, ring_mask, sampling, index=None) 
    if timeperframe is None: 
        times = np.arange( FD.end - FD.beg  ) + FD.beg # get the time for each frame
    else:
        times = ( FD.beg + np.arange( FD.end - FD.beg ) )*timeperframe
    num_rings = len( np.unique( ring_mask)[1:] ) 
    
    if plot_:
        fig, ax = plt.subplots(figsize=(8, 8))
        uid = 'uid'
        if 'uid' in kwargs.keys():
            uid = kwargs['uid'] 
        
        ax.set_title("uid= %s--Mean intensity of each ROI"%uid)
        for i in range(num_rings):
            ax.plot( times, mean_int_sets[:,i], label="ROI "+str(i+1),marker = 'o', ls='-')
            if timeperframe is not None:   
                ax.set_xlabel("Time, sec")
            else:
                ax.set_xlabel("Frame")
            ax.set_ylabel("Mean Intensity")
        ax.legend(loc = 'best',fontsize='x-small') 
                
        if save:
            #dt =datetime.now()
            #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)             
            path = kwargs['path']              
            #fp = path + "uid= %s--Mean intensity of each ring-"%uid + CurTime + '.png' 
            fp = path + "uid=%s--Mean-intensity-of-each-ROI-"%uid  + '.png' 
            fig.savefig( fp, dpi=fig.dpi)
            
            save_arrays( np.hstack( [times.reshape(len(times),1), mean_int_sets]),
                        label=  ['frame']+ ['ROI_%d'%i for i in range( num_rings ) ],
                        filename='uid=%s-t-ROIs'%uid, path= path  )  
        
        plt.show()
        
    return times, mean_int_sets


 



        
    