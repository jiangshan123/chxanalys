"""
Dec 10, 2015 Developed by Y.G.@CHX 
yuzhang@bnl.gov
This module is for the SAXS XPCS analysis 
"""


from chxanalys_debug.chx_libs import  ( colors, colors_copy, markers, markers_copy,
                                 colors_,  markers_, Figure, RUN_GUI)
from chxanalys_debug.chx_generic_functions import *
from scipy.special import erf

from chxanalys_debug.chx_compress_analysis import ( compress_eigerdata, read_compressed_eigerdata,
                                             init_compress_eigerdata,
                                             Multifile,get_each_ring_mean_intensityc,get_avg_imgc, mean_intensityc )

from chxanalys_debug.chx_correlationc import ( cal_g2c,Get_Pixel_Arrayc,auto_two_Arrayc,get_pixelist_interp_iq,)
from chxanalys_debug.chx_correlationp import ( cal_g2p)

    
markers =  ['D',  'd', 'o', 'v', 'H', 'x', '*', '>', 'p',
             's', '_', 'h', '+',             
             '<',  '^', '8', '.', '|', ',', '3', '2', '4', '1',]

markers = np.array(   markers *10 )

colors = np.array( ['darkorange', 'mediumturquoise', 'seashell', 'mediumaquamarine', 'darkblue', 
           'yellowgreen', 'cyan', 'mintcream', 'royalblue', 'springgreen', 'slategray',
           'yellow', 'slateblue', 'darkslateblue', 'papayawhip', 'bisque', 'firebrick', 
           'burlywood',  'dodgerblue', 'dimgrey', 'chartreuse', 'deepskyblue', 'honeydew', 
           'orchid',  'teal', 'steelblue', 'plum', 'limegreen', 'antiquewhite', 
           'linen', 'saddlebrown', 'grey', 'khaki',  'hotpink', 'darkslategray', 
           'forestgreen',  'lightsalmon', 'turquoise', 'navajowhite', 'peachpuff',
           'greenyellow', 'darkgrey', 'darkkhaki', 'slategrey', 'indigo',
           'darkolivegreen', 'aquamarine', 'moccasin', 'beige', 'ivory', 'olivedrab',
           'whitesmoke', 'paleturquoise', 'blueviolet', 'tomato', 'aqua', 'palegoldenrod', 
           'cornsilk', 'navy', 'mediumvioletred', 'palevioletred', 'aliceblue', 'azure', 
             'orangered', 'lightgrey', 'lightpink', 'orange', 'lightsage', 'wheat', 
           'darkorchid', 'mediumslateblue', 'lightslategray', 'green', 'lawngreen', 'tan', 
           'mediumseagreen', 'darksalmon', 'pink', 'oldlace', 'sienna', 'dimgray', 'fuchsia',
           'lemonchiffon', 'maroon', 'salmon', 'gainsboro', 'indianred', 'crimson',
           'olive', 'mistyrose', 'lime', 'lightblue', 'darkgreen', 'lightgreen', 'deeppink', 
           'palegreen', 'thistle', 'lightcoral', 'lightgray', 'lightskyblue', 'mediumspringgreen', 
           'mediumblue', 'peru', 'lightgoldenrodyellow', 'darkseagreen', 'mediumorchid', 
           'coral', 'lightyellow', 'chocolate', 'lavenderblush', 'darkred', 'lightseagreen', 
           'darkviolet', 'lightcyan', 'cadetblue', 'blanchedalmond', 'midnightblue', 
           'darksage', 'lightsteelblue', 'darkcyan', 'floralwhite', 'darkgray', 'magenta',
           'lavender', 'sandybrown', 'cornflowerblue', 'sage',  'gray', 
           'mediumpurple', 'lightslategrey', 'powderblue',  'seagreen', 'skyblue',
           'silver', 'darkmagenta', 'darkslategrey', 'darkgoldenrod', 'rosybrown', 
           'goldenrod',   'darkturquoise', 
                    'gold', 'purple', 
                  'violet', 'blue',  'brown', 'red', 'black'] *10 )
colors = colors[::-1]
colors_ = itertools.cycle(   colors  )
#colors_ = itertools.cycle(sorted_colors_ )
markers_ = itertools.cycle( markers )
    
    
    
def bin_1D(x, y, nx=None, min_x=None, max_x=None):
    """
    Bin the values in y based on their x-coordinates

    Parameters
    ----------
    x : array
        position
    y : array
        intensity
    nx : integer, optional
        number of bins to use defaults to default bin value
    min_x : float, optional
        Left edge of first bin defaults to minimum value of x
    max_x : float, optional
        Right edge of last bin defaults to maximum value of x

    Returns
    -------
    edges : array
        edges of bins, length nx + 1

    val : array
        sum of values in each bin, length nx

    count : array
        The number of counts in each bin, length nx
    """

    # handle default values
    if min_x is None:
        min_x = np.min(x)
    if max_x is None:
        max_x = np.max(x)
    if nx is None:
        nx = int(max_x - min_x) 

    #print ( min_x, max_x, nx)    
    
    
    # use a weighted histogram to get the bin sum
    bins = np.linspace(start=min_x, stop=max_x, num=nx+1, endpoint=True)
    #print (x)
    #print (bins)
    val, _ = np.histogram(a=x, bins=bins, weights=y)
    # use an un-weighted histogram to get the counts
    count, _ = np.histogram(a=x, bins=bins)
    # return the three arrays
    return bins, val, count



def circular_average(image, calibrated_center, threshold=0, nx=None,
                     pixel_size=(1, 1),  min_x=None, max_x=None, mask=None):
    """Circular average of the the image data
    The circular average is also known as the radial integration
    Parameters
    ----------
    image : array
        Image to compute the average as a function of radius
    calibrated_center : tuple
        The center of the image in pixel units
        argument order should be (row, col)
    threshold : int, optional
        Ignore counts above `threshold`
        default is zero
    nx : int, optional
        number of bins in x
        defaults is 100 bins
    pixel_size : tuple, optional
        The size of a pixel (in a real unit, like mm).
        argument order should be (pixel_height, pixel_width)
        default is (1, 1)
    min_x : float, optional number of pixels
        Left edge of first bin defaults to minimum value of x
    max_x : float, optional number of pixels
        Right edge of last bin defaults to maximum value of x
    Returns
    -------
    bin_centers : array
        The center of each bin in R. shape is (nx, )
    ring_averages : array
        Radial average of the image. shape is (nx, ).
    """
    radial_val = utils.radial_grid(calibrated_center, image.shape, pixel_size)     
    
    if mask is not None:  
        #maks = np.ones_like(  image )
        mask = np.array( mask, dtype = bool)
        binr = radial_val[mask]
        image_mask =     np.array( image )[mask]
        
    else:        
        binr = np.ravel( radial_val ) 
        image_mask = np.ravel(image) 
        
    #if nx is None: #make a one-pixel width q
    #   nx = int( max_r - min_r)
    #if min_x is None:
    #    min_x= int( np.min( binr))
    #    min_x_= int( np.min( binr)/(np.sqrt(pixel_size[1]*pixel_size[0] )))
    #if max_x is None:
    #    max_x = int( np.max(binr )) 
    #    max_x_ = int( np.max(binr)/(np.sqrt(pixel_size[1]*pixel_size[0] ))  )
    #if nx is None:
    #    nx = max_x_ - min_x_
    
    #binr_ = np.int_( binr /(np.sqrt(pixel_size[1]*pixel_size[0] )) )
    binr_ =   binr /(np.sqrt(pixel_size[1]*pixel_size[0] ))
    #print ( min_x, max_x, min_x_, max_x_, nx)
    bin_edges, sums, counts = bin_1D(      binr_,
                                           image_mask,
                                           nx=nx,
                                           min_x=min_x,
                                           max_x=max_x)
    
    #print  (len( bin_edges), len( counts) )
    th_mask = counts > threshold
    
    #print  (len(th_mask) )
    ring_averages = sums[th_mask] / counts[th_mask]

    bin_centers = utils.bin_edges_to_centers(bin_edges)[th_mask]
    
    #print (len(  bin_centers ) )

    return bin_centers, ring_averages 

 

def get_circular_average( avg_img, mask, pargs, show_pixel=True,  min_x=None, max_x=None,
                          nx=None, plot_ = False ,   save=False, *argv,**kwargs):   
    """get a circular average of an image        
    Parameters
    ----------
    
    avg_img: 2D-array, the image
    mask: 2D-array  
    pargs: a dict, should contains
        center: the beam center in pixel
        Ldet: sample to detector distance
        lambda_: the wavelength    
        dpix, the pixel size in mm. For Eiger1m/4m, the size is 75 um (0.075 mm)

    nx : int, optional
        number of bins in x
        defaults is 1500 bins
        
    plot_: a boolen type, if True, plot the one-D curve
    plot_qinpixel:a boolen type, if True, the x-axis of the one-D curve is q in pixel; else in real Q
    
    Returns
    -------
    qp: q in pixel
    iq: intensity of circular average
    q: q in real unit (A-1)
     
     
    """   
    
    center, Ldet, lambda_, dpix= pargs['center'],  pargs['Ldet'],  pargs['lambda_'],  pargs['dpix']
    uid = pargs['uid']    
    qp, iq = circular_average(avg_img, 
        center, threshold=0, nx=nx, pixel_size=(dpix, dpix), mask=mask, min_x=min_x, max_x=max_x) 
    qp_ = qp * dpix
    #  convert bin_centers from r [um] to two_theta and then to q [1/px] (reciprocal space)
    two_theta = utils.radius_to_twotheta(Ldet, qp_)
    q = utils.twotheta_to_q(two_theta, lambda_)
    
    #qp = qp_/dpix
    
    if plot_:
        if  show_pixel:       
        
            fig = plt.figure(figsize=(8, 6))
            ax1 = fig.add_subplot(111)
            #ax2 = ax1.twiny()        
            ax1.semilogy(qp, iq, '-o')
            #ax1.semilogy(q,  iq , '-o')
            
            ax1.set_xlabel('q (pixel)')             
            #ax1.set_xlabel('q ('r'$\AA^{-1}$)')
            #ax2.cla()
            ax1.set_ylabel('I(q)')
            title = ax1.set_title('Uid= %s--Circular Average'%uid)      
            
        else:
            fig = plt.figure(figsize=(8, 6))
            ax1 = fig.add_subplot(111)
            ax1.semilogy(q,  iq , '-o') 
            ax1.set_xlabel('q ('r'$\AA^{-1}$)')        
            ax1.set_ylabel('I(q)')
            title = ax1.set_title('uid= %s--Circular Average'%uid)     
            ax2=None 
        
                    
        if 'xlim' in kwargs.keys():
            ax1.set_xlim(    kwargs['xlim']  )    
            x1,x2 =  kwargs['xlim']
            w = np.where( (q >=x1 )&( q<=x2) )[0]                        
            #if ax2 is not None:
            #    ax2.set_xlim(  [ qp[w[0]], qp[w[-1]]]     ) 
            
            
        if 'ylim' in kwargs.keys():
            ax1.set_ylim(    kwargs['ylim']  )        
          
        title.set_y(1.1)
        fig.subplots_adjust(top=0.85)

        
        #if plot_qinpixel:
        #ax2.set_xlabel('q (pixel)')
        #else:
        #ax1.set_xlabel('q ('r'$\AA^{-1}$)')
        #axes.set_xlim(30,  1050)
        #axes.set_ylim(-0.0001, 10000)
        if save:
            #dt =datetime.now()
            #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)
            path = pargs['path']
            #fp = path + 'Uid= %s--Circular Average'%uid + CurTime + '.png'     
            fp = path + 'uid=%s--Circular-Average-'%uid  + '.png'  
            fig.savefig( fp, dpi=fig.dpi)
            
            save_lists(  [q, iq], label=['q_A-1', 'Iq'],  filename='uid=%s-q-Iq'%uid, path= path  )
        
        plt.show()
        
    return  qp, iq, q

 
 
def plot_circular_average( qp, iq, q,  pargs, show_pixel=True,   save=False,return_fig=False, *argv,**kwargs):
    
    if RUN_GUI:
        fig = Figure()
        ax1 = fig.add_subplot(111)
    else:
        fig, ax1 = plt.subplots()

    uid = pargs['uid']

    if  show_pixel:  
        ax1.semilogy(qp, iq, '-o')
        ax1.set_xlabel('q (pixel)')  
        ax1.set_ylabel('I(q)')
        title = ax1.set_title('Uid= %s--Circular Average'%uid)  
    else:
        ax1.semilogy(q,  iq , '-o') 
        ax1.set_xlabel('q ('r'$\AA^{-1}$)')        
        ax1.set_ylabel('I(q)')
        title = ax1.set_title('uid= %s--Circular Average'%uid)     
        ax2=None 


    if 'xlim' in kwargs.keys():
        ax1.set_xlim(    kwargs['xlim']  )    
        x1,x2 =  kwargs['xlim']
        w = np.where( (q >=x1 )&( q<=x2) )[0]                        
        #if ax2 is not None:
        #    ax2.set_xlim(  [ qp[w[0]], qp[w[-1]]]     )             
    if 'ylim' in kwargs.keys():
        ax1.set_ylim(    kwargs['ylim']  )        

    title.set_y(1.1)
    fig.subplots_adjust(top=0.85)

    if save:
        #dt =datetime.now()
        #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)
        path = pargs['path']
        #fp = path + 'Uid= %s--Circular Average'%uid + CurTime + '.png'     
        fp = path + 'uid=%s--Circular-Average-'%uid  + '.png'  
        plt.savefig( fp, dpi=fig.dpi)            
        save_lists(  [q, iq], label=['q_A-1', 'Iq'],  filename='uid=%s-q-Iq'%uid, path= path  )
    if return_fig:
        return fig        


def get_angular_average( avg_img, mask, pargs,   min_r, max_r, 
                        nx=3600, plot_ = False ,   save=False, *argv,**kwargs):   
    """get a angular average of an image        
    Parameters
    ----------
    
    avg_img: 2D-array, the image
    mask: 2D-array  
    pargs: a dict, should contains
        center: the beam center in pixel
        Ldet: sample to detector distance
        lambda_: the wavelength    
        dpix, the pixel size in mm. For Eiger1m/4m, the size is 75 um (0.075 mm)

    nx : int, optional
        number of bins in x
        defaults is 1500 bins
        
    plot_: a boolen type, if True, plot the one-D curve
    plot_qinpixel:a boolen type, if True, the x-axis of the one-D curve is q in pixel; else in real Q
    
    Returns
    -------
    ang: ang in degree
    iq: intensity of circular average
     
     
     
    """   
    
    center, Ldet, lambda_, dpix= pargs['center'],  pargs['Ldet'],  pargs['lambda_'],  pargs['dpix']
    uid = pargs['uid']
    
    angq, ang = angular_average( avg_img,  calibrated_center=center, pixel_size=(dpix,dpix), nx =nx,
                    min_r = min_r , max_r = max_r, mask=mask )
 
    
    if plot_:
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111) 
        ax.plot(angq,  ang , '-o')             
        ax.set_xlabel("angle (deg)")
        ax.set_ylabel("I(ang)")
        #ax.legend(loc = 'best')  
        uid = pargs['uid']
        title = ax.set_title('Uid= %s--t-I(Ang)'%uid)        
        title.set_y(1.01)
        
        if save:
            #dt =datetime.now()
            #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)
            path = pargs['path']
            uid = pargs['uid']
 
            #fp = path + 'Uid= %s--Ang-Iq~t-'%uid + CurTime + '.png'   
            fp = path + 'uid=%s--Ang-Iq-t-'%uid   + '.png'   
            fig.savefig( fp, dpi=fig.dpi)
            
        plt.show()
 
        
    return  angq, ang





def angular_average(image, calibrated_center, threshold=0, nx=1500,
                     pixel_size=(1, 1),  min_r=None, max_r=None, min_x=None, max_x=None, mask=None):
    """Angular_average of the the image data
     
    Parameters
    ----------
    image : array
        Image to compute the average as a function of radius
    calibrated_center : tuple
        The center of the image in pixel units
        argument order should be (row, col)
    threshold : int, optional
        Ignore counts above `threshold`
        default is zero
    nx : int, optional
        number of bins in x
        defaults is 100 bins
    pixel_size : tuple, optional
        The size of a pixel (in a real unit, like mm).
        argument order should be (pixel_height, pixel_width)
        default is (1, 1)
        
    min_r: float, optional number of pixels
        The min r, e.g., the starting radius for angule average
    max_r:float, optional number of pixels
        The max r, e.g., the ending radius for angule average
        max_r - min_r gives the width of the angule average
        
    min_x : float, optional number of pixels
        Left edge of first bin defaults to minimum value of x
    max_x : float, optional number of pixels
        Right edge of last bin defaults to maximum value of x
    Returns
    -------
    bin_centers : array
        The center of each bin in degree shape is (nx, )
    ring_averages : array
        Radial average of the image. shape is (nx, ).
    """
     
    angle_val = utils.angle_grid(calibrated_center, image.shape, pixel_size) 
        
    if min_r is None:
        min_r=0
    if max_r is None:
        max_r = np.sqrt(  (image.shape[0] - calibrated_center[0])**2 +  (image.shape[1] - calibrated_center[1])**2 )    
    r_mask = make_ring_mask( calibrated_center, image.shape, min_r, max_r )
    
    
    if mask is not None:  
        #maks = np.ones_like(  image )
        mask = np.array( mask*r_mask, dtype = bool)
        
        bina = angle_val[mask]
        image_mask =     np.array( image )[mask]
        
    else:        
        bina = np.ravel( angle_val ) 
        image_mask = np.ravel(image*r_mask) 
        
    bin_edges, sums, counts = utils.bin_1D( bina,
                                           image_mask,
                                           nx,
                                           min_x=min_x,
                                           max_x=max_x)
    
    #print (counts)
    th_mask = counts > threshold
    ang_averages = sums[th_mask] / counts[th_mask]

    bin_centers = utils.bin_edges_to_centers(bin_edges)[th_mask]

    return bin_centers*180/np.pi, ang_averages 


def get_t_iqc( FD, frame_edge, mask, pargs, nx=1500, plot_ = False , save=False, *argv,**kwargs):   
    '''Get t-dependent Iq 
    
        Parameters        
        ----------
        data_series:  a image series
        frame_edge: list, the ROI frame regions, e.g., [  [0,100], [200,400] ]
        mask:  a image mask 
        
        nx : int, optional
            number of bins in x
            defaults is 1500 bins
        plot_: a boolen type, if True, plot the time~one-D curve with qp as x-axis
        Returns
        ---------
        qp: q in pixel
        iq: intensity of circular average
        q: q in real unit (A-1)
     
    '''   
       
    Nt = len( frame_edge )
    iqs = list( np.zeros( Nt ) )
    for i in range(Nt):
        t1,t2 = frame_edge[i]
        #print (t1,t2)        
        avg_img = get_avg_imgc( FD, beg=t1,end=t2, sampling = 1, plot_ = False )
        qp, iqs[i], q = get_circular_average( avg_img, mask,pargs, nx=nx,
                           plot_ = False)
        
    if plot_:
        fig,ax = plt.subplots(figsize=(8, 6))
        for i in range(  Nt ):
            t1,t2 = frame_edge[i]
            ax.semilogy(q, iqs[i], label="frame: %s--%s"%( t1,t2) )
            #ax.set_xlabel("q in pixel")
            ax.set_xlabel('Q 'r'($\AA^{-1}$)')
            ax.set_ylabel("I(q)")
            
        if 'xlim' in kwargs.keys():
            ax.set_xlim(    kwargs['xlim']  )    
        if 'ylim' in kwargs.keys():
            ax.set_ylim(    kwargs['ylim']  )
 

        ax.legend(loc = 'best')  
        
        uid = pargs['uid']
        title = ax.set_title('uid= %s--t~I(q)'%uid)        
        title.set_y(1.01)
        if save:
            #dt =datetime.now()
            #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)
            path = pargs['path']
            uid = pargs['uid']
            #fp = path + 'uid= %s--Iq~t-'%uid + CurTime + '.png'  
            fp = path + 'uid=%s--Iq-t-'%uid + '.png'  
            fig.savefig( fp, dpi=fig.dpi)
            
            save_arrays(  np.vstack( [q, np.array(iqs)]).T, 
                        label=  ['q_A-1']+ ['Fram-%s-%s'%(t[0],t[1]) for t in frame_edge],
                        filename='uid=%s-q-Iqt'%uid, path= path  )
            
        plt.show()        
    
    return qp, np.array( iqs ),q

 

def get_distance(p1,p2):
    '''Calc the distance between two point'''
    return np.sqrt(  (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2   )


def calc_q(L,a,wv):
    ''' calc_q(L,a,wv) - calculate the q value for length L, transverse
            distance a and wavelength wv.
        Use this to calculate the speckle size
        
        L - sample to detector distance (mm)
        a - pixel size transverse length from beam direction (mm)
        wv - wavelength
        Units of L and a should match and resultant q is in inverse units of wv.
    '''
    theta = np.arctan2(a,L)
    q = 4*np.pi*np.sin(theta/2.)/wv
    return q




def get_t_iq( data_series, frame_edge, mask, pargs, nx=1500, plot_ = False , save=False, *argv,**kwargs):   
    '''Get t-dependent Iq 
    
        Parameters        
        ----------
        data_series:  a image series
        frame_edge: list, the ROI frame regions, e.g., [  [0,100], [200,400] ]
        mask:  a image mask 
        
        nx : int, optional
            number of bins in x
            defaults is 1500 bins
        plot_: a boolen type, if True, plot the time~one-D curve with qp as x-axis

        Returns
        ---------
        qp: q in pixel
        iq: intensity of circular average
        q: q in real unit (A-1)
     
    '''   
       
    Nt = len( frame_edge )
    iqs = list( np.zeros( Nt ) )
    for i in range(Nt):
        t1,t2 = frame_edge[i]
        #print (t1,t2)
        avg_img = get_avg_img( data_series[t1:t2], sampling = 1,
                         plot_ = False )
        qp, iqs[i], q = get_circular_average( avg_img, mask,pargs, nx=nx,
                           plot_ = False)
        
    if plot_:
        fig,ax = plt.subplots(figsize=(8, 6))
        for i in range(  Nt ):
            t1,t2 = frame_edge[i]
            ax.semilogy(q, iqs[i], label="frame: %s--%s"%( t1,t2) )
            #ax.set_xlabel("q in pixel")
            ax.set_xlabel('Q 'r'($\AA^{-1}$)')
            ax.set_ylabel("I(q)")
            
        if 'xlim' in kwargs.keys():
            ax.set_xlim(    kwargs['xlim']  )    
        if 'ylim' in kwargs.keys():
            ax.set_ylim(    kwargs['ylim']  )
 

        ax.legend(loc = 'best')  
        
        uid = pargs['uid']
        title = ax.set_title('uid=%s--t-I(q)'%uid)        
        title.set_y(1.01)
        if save:
            #dt =datetime.now()
            #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)
            path = pargs['path']
            uid = pargs['uid']
            #fp = path + 'Uid= %s--Iq~t-'%uid + CurTime + '.png'         
            fp = path + 'uid=%s--Iq-t-'%uid  + '.png'    
            fig.savefig( fp, dpi=fig.dpi)
            
        plt.show()
        
    
    return qp, np.array( iqs ),q


    
def get_t_ang( data_series, frame_edge, mask, center, pixel_size, min_r, max_r,pargs,
                nx=1500, plot_ = False , save=False, *argv,**kwargs):   
    '''Get t-dependent angule intensity 
    
        Parameters        
        ----------
        data_series:  a image series
        frame_edge: list, the ROI frame regions, e.g., [  [0,100], [200,400] ]
        mask:  a image mask 
        
        pixel_size : tuple, optional
            The size of a pixel (in a real unit, like mm).
            argument order should be (pixel_height, pixel_width)
            default is (1, 1)
        center: the beam center in pixel 
        min_r: float, optional number of pixels
            The min r, e.g., the starting radius for angule average
        max_r:float, optional number of pixels
            The max r, e.g., the ending radius for angule average
            
            max_r - min_r gives the width of the angule average
        
        nx : int, optional
            number of bins in x
            defaults is 1500 bins
        plot_: a boolen type, if True, plot the time~one-D curve with qp as x-axis

        Returns
        ---------
        qp: q in pixel
        iq: intensity of circular average
        q: q in real unit (A-1)
     
    '''   
       
    Nt = len( frame_edge )
    iqs = list( np.zeros( Nt ) )
    for i in range(Nt):
        t1,t2 = frame_edge[i]
        #print (t1,t2)
        avg_img = get_avg_img( data_series[t1:t2], sampling = 1,
                         plot_ = False )
        qp, iqs[i] = angular_average( avg_img, center, pixel_size=pixel_size, 
                                     nx=nx, min_r=min_r, max_r = max_r, mask=mask ) 
        
    if plot_:
        fig,ax = plt.subplots(figsize=(8, 8))
        for i in range(  Nt ):
            t1,t2 = frame_edge[i]
            #ax.semilogy(qp* 180/np.pi, iqs[i], label="frame: %s--%s"%( t1,t2) )
            ax.plot(qp, iqs[i], label="frame: %s--%s"%( t1,t2) )
            ax.set_xlabel("angle (deg)")
            ax.set_ylabel("I(ang)")
        ax.legend(loc = 'best')  
        uid = pargs['uid']
        title = ax.set_title('Uid= %s--t-I(Ang)'%uid)        
        title.set_y(1.01)
        
        if save:
            #dt =datetime.now()
            #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)
            path = pargs['path']
            uid = pargs['uid']
            #fp = path + 'Uid= %s--Ang-Iq~t-'%uid + CurTime + '.png'         
            fp = path + 'uid=%s--Ang-Iq-t-'%uid  + '.png'         
            fig.savefig( fp, dpi=fig.dpi)
            
        plt.show()
        
    
    return qp, np.array( iqs ) 


def make_ring_mask(center, shape, min_r, max_r  ):
    """
    Make a ring mask.

    Parameters
    ----------
    center : tuple
        point in image where r=0; may be a float giving subpixel precision.
        Order is (rr, cc).
    shape: tuple
        Image shape which is used to determine the maximum extent of output
        pixel coordinates. Order is (rr, cc).        

    min_r: float, optional number of pixels
        The min r, e.g., the starting radius of the ring
    max_r:float, optional number of pixels
        The max r, e.g., the ending radius of the ring
        max_r - min_r gives the width of the ring
    Returns
    -------
    ring_mask : array


    """
    r_val = utils.radial_grid(center, shape, [1.,1.] ) 
    r_mask = np.zeros_like( r_val, dtype=np.int32)
    r_mask[np.where(  (r_val >min_r)  & (r_val < max_r ) )] = 1

    return r_mask   


def _make_roi(coords, edges, shape):
    """ Helper function to create ring rois and bar rois
    Parameters
    ----------
    coords : array
        shape is image shape
    edges : list
        List of tuples of inner (left or top) and outer (right or bottom)
        edges of each roi.
        e.g., edges=[(1, 2), (11, 12), (21, 22)]
    shape : tuple
        Shape of the image in which to create the ROIs
        e.g., shape=(512, 512)
    Returns
    -------
    label_array : array
        Elements not inside any ROI are zero; elements inside each
        ROI are 1, 2, 3, corresponding to the order they are
        specified in `edges`.
        Has shape=`image shape`
    """
    label_array = np.digitize(coords, edges, right=False)
    # Even elements of label_array are in the space between rings.
    label_array = (np.where(label_array % 2 != 0, label_array, 0) + 1) // 2
    return label_array.reshape(shape)


def angulars(edges, center, shape):
    """
    Draw annual (angluar-shaped) shaped regions of interest.
    Each ring will be labeled with an integer. Regions outside any ring will
    be filled with zeros.
    Parameters
    ----------
    edges: list
        giving the inner and outer angle in unit of radians
        e.g., [(1, 2), (11, 12), (21, 22)]
    center: tuple
        point in image where r=0; may be a float giving subpixel precision.
        Order is (rr, cc).
    shape: tuple
        Image shape which is used to determine the maximum extent of output
        pixel coordinates. Order is (rr, cc).
    Returns
    -------
    label_array : array
        Elements not inside any ROI are zero; elements inside each
        ROI are 1, 2, 3, corresponding to the order they are specified
        in edges.
    """
    edges = np.atleast_2d(np.asarray(edges)).ravel() 
    if not 0 == len(edges) % 2:
        raise ValueError("edges should have an even number of elements, "
                         "giving inner, outer radii for each angular")
    if not np.all( np.diff(edges) > 0):         
        raise ValueError("edges are expected to be monotonically increasing, "
                         "giving inner and outer radii of each angular from "
                         "r=0 outward")

    angle_val = utils.angle_grid( center,  shape) .ravel()        
     
    return _make_roi(angle_val, edges, shape)




    

def get_angular_mask( mask,  inner_angle=0, outer_angle = 360, width = None, edges = None,
                     num_angles = 12, center = None, dpix=[1,1], flow_geometry=False    ):
     
    ''' 
    mask: 2D-array 
    inner_angle # the starting angle in unit of degree
    outer_angle #  the ending angle in unit of degree
    width       # width of each angle, in degree, default is None, there is no gap between the neighbour angle ROI
    edges: default, None. otherwise, give a customized angle edges
    num_angles    # number of angles
     
    center: the beam center in pixel    
    dpix, the pixel size in mm. For Eiger1m/4m, the size is 75 um (0.075 mm)
    flow_geometry: if True, the angle should be between 0 and 180. the map will be a center inverse symmetry
    
    Returns
    -------
    ang_mask: a ring mask, np.array
    ang_center: ang in unit of degree
    ang_val: ang edges in degree
    
    '''
    
    #center, Ldet, lambda_, dpix= pargs['center'],  pargs['Ldet'],  pargs['lambda_'],  pargs['dpix']
    
    #spacing =  (outer_radius - inner_radius)/(num_rings-1) - 2    # spacing between rings
    #inner_angle,outer_angle = np.radians(inner_angle),  np.radians(outer_angle)
    
    #if edges is  None:
    #    ang_center =   np.linspace( inner_angle,outer_angle, num_angles )  
    #    edges = np.zeros( [ len(ang_center), 2] )
    #    if width is None:
    #        width = ( -inner_angle + outer_angle)/ float( num_angles -1 + 1e-10 )
    #    else:
    #        width =  np.radians( width )
    #    edges[:,0],edges[:,1] = ang_center - width/2, ang_center + width/2 
        

    if flow_geometry:
        if inner_angle<0:
            print('In this flow_geometry, the inner_angle should be larger than 0')
        if outer_angle >180:
            print('In this flow_geometry, the out_angle should be smaller than 180')
            

    if edges is None:
        if num_angles!=1:
            spacing =  (outer_angle - inner_angle - num_angles* width )/(num_angles-1)      # spacing between rings
        else:
            spacing = 0
        edges1 = roi.ring_edges(inner_angle, width, spacing, num_angles) 

    #print (edges)
    angs = angulars( np.radians( edges1 ), center, mask.shape)    
    ang_center = np.average(edges1, axis=1)        
    ang_mask = angs*mask
    ang_mask = np.array(ang_mask, dtype=int)
        
    if flow_geometry:
        outer_angle -= 180
        inner_angle -= 180 
        if edges is None:
            edges2 = roi.ring_edges(inner_angle, width, spacing, num_angles)
        #print (edges)
        angs2 = angulars( np.radians( edges2 ), center, mask.shape)
        ang_mask2 = angs2*mask
        ang_mask2 = np.array(ang_mask2, dtype=int)        
        ang_mask +=  ang_mask2    
    
    labels, indices = roi.extract_label_indices(ang_mask)
    nopr = np.bincount( np.array(labels, dtype=int) )[1:]
   
    if len( np.where( nopr ==0 )[0] !=0):
        print (nopr)
        print ("Some angs contain zero pixels. Please redefine the edges.")      
    return ang_mask, ang_center, edges1


       
def two_theta_to_radius(dist_sample, two_theta):
    """
    Converts scattering angle (2:math:`2\\theta`) to radius (from the calibrated center)
    with known detector to sample distance.

    Parameters
    ----------
    dist_sample : float
        distance from the sample to the detector (mm)
        
    two_theta : array
        An array of :math:`2\\theta` values

    Returns
    -------        
    radius : array
        The L2 norm of the distance (mm) of each pixel from the calibrated center.
    """
    return np.tan(two_theta) * dist_sample


def get_ring_mask(  mask, inner_radius=40, outer_radius = 762, width = 6, num_rings = 12,
                  edges=None, unit='pixel',pargs=None   ):
    
#def get_ring_mask(  mask, inner_radius= 0.0020, outer_radius = 0.009, width = 0.0002, num_rings = 12,
#                  edges=None, unit='pixel',pargs=None   ):     
    ''' 
    mask: 2D-array 
    inner_radius #radius of the first ring
    outer_radius # radius of the last ring
    width       # width of each ring
    num_rings    # number of rings
    pargs: a dict, should contains
        center: the beam center in pixel
        Ldet: sample to detector distance
        lambda_: the wavelength, in unit of A    
        dpix, the pixel size in mm. For Eiger1m/4m, the size is 75 um (0.075 mm)
        unit: if pixel, all the radius inputs are in unit of pixel
              else: should be in unit of A-1
    Returns
    -------
    ring_mask: a ring mask, np.array
    q_ring_center: q in real unit (A-1)
    q_ring_val: q edges in A-1 
    
    '''
    
    center, Ldet, lambda_, dpix= pargs['center'],  pargs['Ldet'],  pargs['lambda_'],  pargs['dpix']
    
    #spacing =  (outer_radius - inner_radius)/(num_rings-1) - 2    # spacing between rings
    #qc = np.int_( np.linspace( inner_radius,outer_radius, num_rings ) )
    #edges = np.zeros( [ len(qc), 2] )
    #if width%2: 
    #   edges[:,0],edges[:,1] = qc - width//2,  qc + width//2 +1
    #else:
    #    edges[:,0],edges[:,1] = qc - width//2,  qc + width//2 
    
    #  find the edges of the required rings
    if edges is None:
        if num_rings!=1:
            spacing =  (outer_radius - inner_radius - num_rings* width )/(num_rings-1)      # spacing between rings
        else:
            spacing = 0
        edges = roi.ring_edges(inner_radius, width, spacing, num_rings)    
   
    if (unit=='pixel') or (unit=='p'):
        two_theta = utils.radius_to_twotheta(Ldet, edges*dpix)
        q_ring_val = utils.twotheta_to_q(two_theta, lambda_)
    else: #in unit of A-1 
        two_theta = utils.q_to_twotheta( edges, lambda_)
        q_ring_val =  edges
        edges = two_theta_to_radius(Ldet,two_theta)/dpix  #converto pixel  
    
    q_ring_center = np.average(q_ring_val, axis=1)  
    
    rings = roi.rings(edges, center, mask.shape)
    ring_mask = rings*mask
    ring_mask = np.array(ring_mask, dtype=int)    
    
    labels, indices = roi.extract_label_indices(ring_mask)
    nopr = np.bincount( np.array(labels, dtype=int) )[1:]
   
    if len( np.where( nopr ==0 )[0] !=0):
        print (nopr)
        print ("Some rings contain zero pixels. Please redefine the edges.")      
    return ring_mask, q_ring_center, q_ring_val

 
    


def get_ring_anglar_mask(ring_mask, ang_mask,    
                         q_ring_center, ang_center   ):
    '''get   ring_anglar mask  '''
    
    ring_max = ring_mask.max()
    
    ang_mask_ = np.zeros( ang_mask.shape  )
    ind = np.where(ang_mask!=0)
    ang_mask_[ind ] =  ang_mask[ ind ] + 1E9  #add some large number to qr
    
    dumy_ring_mask = np.zeros( ring_mask.shape  )
    dumy_ring_mask[ring_mask==1] =1
    dumy_ring_ang = dumy_ring_mask * ang_mask
    real_ang_lab =   np.int_( np.unique( dumy_ring_ang )[1:] ) -1
    
    ring_ang = ring_mask * ang_mask_  
    
    #convert label_array_qzr to [1,2,3,...]
    ura = np.unique( ring_ang )[1:]
    
    ur = np.unique( ring_mask )[1:]
    ua = np.unique( ang_mask )[real_ang_lab]
        
    
    ring_ang_ = np.zeros_like( ring_ang )
    newl = np.arange( 1, len(ura)+1)
    #newl = np.int_( real_ang_lab )   
    
    
    rc= [  [ q_ring_center[i]]*len( ua ) for i in range(len( ur ))  ]
    ac =list( ang_center[ua]) * len( ur )
    
    #rc =list( q_ring_center) * len( ua )
    #ac= [  [ ang_center[i]]*len( ur ) for i in range(len( ua ))  ]
    
    for i, label in enumerate(ura):
        #print (i, label)
        ring_ang_.ravel()[ np.where(  ring_ang.ravel() == label)[0] ] = newl[i]  
    
    
    return   np.int_(ring_ang_), np.concatenate( np.array( rc )),  np.array( ac ) 




def show_ring_ang_roi( data, rois,   alpha=0.3, save=False, *argv,**kwargs): 
        
    ''' 
    May 16, 2016, Y.G.@CHX
    plot a saxs image with rois( a label array) 
    
    Parameters:
        data: 2-D array, a gisaxs image 
        rois:  2-D array, a label array         
 
         
    Options:
        alpha:  transparency of the label array on top of data
        
    Return:
         a plot of a qzr map of a gisaxs image with rois( a label array)
   
    
    Examples:        
        show_qzr_roi( avg_imgr, box_maskr, inc_x0, ticks)
         
    '''
      
        
        
    #import matplotlib.pyplot as plt    
    #import copy
    #import matplotlib.cm as mcm
    
    #cmap='viridis'
    #_cmap = copy.copy((mcm.get_cmap(cmap)))
    #_cmap.set_under('w', 0)
     
    avg_imgr, box_maskr = data, rois
    num_qzr = len(np.unique( box_maskr)) -1
    fig, ax = plt.subplots(figsize=(8,12))
    ax.set_title("ROI--Labeled Array on Data")
    im,im_label = show_label_array_on_image(ax, avg_imgr, box_maskr, imshow_cmap='viridis',
                            cmap='Paired', alpha=alpha,
                             vmin=0.01, vmax=30. ,  origin="lower")


    for i in range( 1, num_qzr+1 ):
        ind =  np.where( box_maskr == i)[1]
        indz =  np.where( box_maskr == i)[0]
        c = '%i'%i
        y_val = int( indz.mean() )

        x_val = int( ind.mean() )
        #print (xval, y)
        ax.text(x_val, y_val, c, va='center', ha='center')

        #print (x_val1,x_val2)

    
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    plt.colorbar(im, cax=cax)
    
        
    if save:
        #dt =datetime.now()
        #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)             
        path = kwargs['path'] 
        if 'uid' in kwargs:
            uid = kwargs['uid']
        else:
            uid = 'uid'
        #fp = path + "uid= %s--Waterfall-"%uid + CurTime + '.png'     
        fp = path + "uid=%s--ROI-on-image-"%uid  + '.png'    
        fig.savefig( fp, dpi=fig.dpi) 
    
    #ax.set_xlabel(r'$q_r$', fontsize=22)
    #ax.set_ylabel(r'$q_z$',fontsize=22)

    plt.show()
 
    
    
def plot_qIq_with_ROI( q, iq, q_ring_center, logs=True, save=False, return_fig = False, *argv,**kwargs):   
    '''Aug 6, 2016, Y.G.@CHX 
    plot q~Iq with interested q rings'''

    uid = 'uid'
    if 'uid' in kwargs.keys():
        uid = kwargs['uid']        

    if RUN_GUI:
        fig = Figure(figsize=(8, 6))
        axes = fig.add_subplot(111)
    else:
        fig, axes = plt.subplots(figsize=(8, 6))    
    
    if logs:
        axes.semilogy(q, iq, '-o')
    else:        
        axes.plot(q,  iq, '-o')
        
    axes.set_title('uid= %s--Circular Average with the Q ring values'%uid)
    axes.set_ylabel('I(q)')
    axes.set_xlabel('Q 'r'($\AA^{-1}$)')
    #axes.set_xlim(0, 0.02)
    #axes.set_xlim(-0.00001, 0.1)
    #axes.set_ylim(-0.0001, 10000)
    #axes.set_ylim(0, 100)
    
    if 'xlim' in kwargs.keys():
         axes.set_xlim(    kwargs['xlim']  )    
    if 'ylim' in kwargs.keys():
         axes.set_ylim(    kwargs['ylim']  )
 
        
        
    num_rings = len( np.unique( q_ring_center) )
    for i in range(num_rings):
        axes.axvline(q_ring_center[i] )#, linewidth = 5  )
        
    if save:
        #dt =datetime.now()
        #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)             
        path = kwargs['path'] 
        if 'uid' in kwargs:
            uid = kwargs['uid']
        else:
            uid = 'uid'
        #fp = path + "uid= %s--Waterfall-"%uid + CurTime + '.png'     
        fp = path + "uid=%s--ROI-on-Iq-"%uid  + '.png'    
        fig.savefig( fp, dpi=fig.dpi) 
    #plt.show()
    if return_fig:
        return fig, axes 


    
def get_each_ring_mean_intensity( data_series, ring_mask, sampling, timeperframe, plot_ = True , save=False, *argv,**kwargs):   
    
    """
    get time dependent mean intensity of each ring
    """
    mean_int_sets, index_list = roi.mean_intensity(np.array(data_series[::sampling]), ring_mask) 
    
    times = np.arange(len(data_series))*timeperframe  # get the time for each frame
    num_rings = len( np.unique( ring_mask)[1:] )
    if plot_:
        fig, ax = plt.subplots(figsize=(8, 8))
        uid = 'uid'
        if 'uid' in kwargs.keys():
            uid = kwargs['uid'] 
        
        ax.set_title("uid= %s--Mean intensity of each ring"%uid)
        for i in range(num_rings):
            ax.plot( mean_int_sets[:,i], label="Ring "+str(i+1),marker = 'o', ls='-')
            ax.set_xlabel("Time")
            ax.set_ylabel("Mean Intensity")
        ax.legend(loc = 'best') 
                
        if save:
            #dt =datetime.now()
            #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)             
            path = kwargs['path']              
            #fp = path + "Uid= %s--Mean intensity of each ring-"%uid + CurTime + '.png'     
            fp = path + "uid=%s--Mean-intensity-of-each-ROI-"%uid   + '.png'   
            
            fig.savefig( fp, dpi=fig.dpi)
        
        plt.show()
    return times, mean_int_sets







def plot_saxs_g2( g2, taus, res_pargs=None,one_plot=False, ylabel='g2', return_fig=False,tight=True,*argv,**kwargs):     
    '''plot g2 results, 
       g2: one-time correlation function
       taus: the time delays  
       res_pargs, a dict, can contains
           uid/path/qr_center/qz_center/
       kwargs: can contains
           vlim: [vmin,vmax]: for the plot limit of y, the y-limit will be [vmin * min(y), vmx*max(y)]
           ylim/xlim: the limit of y and x
       
       e.g.
       plot_gisaxs_g2( g2b, taus= np.arange( g2b.shape[0]) *timeperframe, q_ring_center = q_ring_center, vlim=[.99, 1.01] )
           
      ''' 

    
    if res_pargs is not None:
        uid = res_pargs['uid'] 
        path = res_pargs['path'] 
        q_ring_center = res_pargs[ 'q_ring_center']
    else:        
        if 'uid' in kwargs.keys():
            uid = kwargs['uid'] 
        else:
            uid = 'uid'
        if 'q_ring_center' in kwargs.keys():
            q_ring_center = kwargs[ 'q_ring_center']
        else:
            q_ring_center = np.arange(  g2.shape[1] )
        if 'path' in kwargs.keys():
            path = kwargs['path'] 
        else:
            path = ''    
    num_rings = g2.shape[1]
    sx = int(round(np.sqrt(num_rings)) )
    if num_rings%sx == 0: 
        sy = int(num_rings/sx)
    else:
        sy=int(num_rings/sx+1)      
    #print (num_rings)
    if not one_plot:    
        if num_rings!=1:
            if RUN_GUI:
                fig = Figure(figsize=(12, 10))
                ax = fig.add_subplot(111)
            else:
                fig, ax = plt.subplots(figsize=(12, 10))
            plt.axis('off')
            #plt.axes(frameon=False)    
            plt.xticks([])
            plt.yticks([])        
            
        else:
            if RUN_GUI:
                fig = Figure(figsize=(8,8))                
            else:
                fig = plt.subplots(figsize=(8,8))
        plt.title('uid=%s'%uid,fontsize=20, y =1.06)        
        for i in range(num_rings):
            ax = fig.add_subplot(sx, sy, i+1 )
            ax.set_ylabel("g2") 
            ax.set_title(" Q= " + '%.5f  '%(q_ring_center[i]) + r'$\AA^{-1}$' )#, fontsize=12)
            y=g2[:, i]
            ax.semilogx(taus, y, '-o', markersize=6) 
            #ax.set_ylim([min(y)*.95, max(y[1:])*1.05 ])
            if 'ylim' in kwargs:
                ax.set_ylim( kwargs['ylim'])
            elif 'vlim' in kwargs:
                if kwargs['vlim'] is not None:
                    vmin, vmax =kwargs['vlim']
                    ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])
            else:
                pass
            if 'xlim' in kwargs:
                ax.set_xlim( kwargs['xlim'])

    else:
        if RUN_GUI:
            fig = Figure(figsize=(8,8))                
        else:
            fig = plt.subplots(figsize=(8,8))        
           
        plt.title('uid=%s'%uid,fontsize=20, y =1.06) 
        ax = fig.add_subplot(111 )
        ax.set_ylabel(ylabel) 
        for i in range(num_rings):
            y=g2[:, i]
            ax.semilogx(taus, y, '-%s'%next(markers), markersize=6, 
                        label = "Q= " + '%.5f  '%(q_ring_center[i]) + r'$\AA^{-1}$') 
            #ax.set_ylim([min(y)*.95, max(y[1:])*1.05 ])
        if 'ylim' in kwargs:
            ax.set_ylim( kwargs['ylim'])
        elif 'vlim' in kwargs:
            vmin, vmax =kwargs['vlim']
            ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])
        else:
            pass
        if 'xlim' in kwargs:
            ax.set_xlim( kwargs['xlim'])
        plt.legend(loc='best', fontsize=6)        
    fp = path + 'uid=%s--%s-'%(uid,ylabel)   + '.png'
    if tight:
        fig.set_tight_layout(True)
    plt.savefig( fp, dpi=fig.dpi) 
    if return_fig:
        return fig    
 
def plot_saxs_g4( g4, taus, res_pargs=None, return_fig=False, *argv,**kwargs):     
    '''plot g2 results, 
       g2: one-time correlation function
       taus: the time delays  
       res_pargs, a dict, can contains
           uid/path/qr_center/qz_center/
       kwargs: can contains
           vlim: [vmin,vmax]: for the plot limit of y, the y-limit will be [vmin * min(y), vmx*max(y)]
           ylim/xlim: the limit of y and x
       
       e.g.
       plot_gisaxs_g4( g4, taus= np.arange( g4.shape[0]) *timeperframe, q_ring_center = q_ring_center, vlim=[.99, 1.01] )
           
      ''' 

    
    if res_pargs is not None:
        uid = res_pargs['uid'] 
        path = res_pargs['path'] 
        q_ring_center = res_pargs[ 'q_ring_center']

    else:
        
        if 'uid' in kwargs.keys():
            uid = kwargs['uid'] 
        else:
            uid = 'uid'

        if 'q_ring_center' in kwargs.keys():
            q_ring_center = kwargs[ 'q_ring_center']
        else:
            q_ring_center = np.arange(  g4.shape[1] )

        if 'path' in kwargs.keys():
            path = kwargs['path'] 
        else:
            path = ''
    
    if 'logx' in kwargs.keys():
        logx = kwargs['logx'] 
    else:
        logx =  False

    
    num_rings = g4.shape[1]
    sx = int(round(np.sqrt(num_rings)) )
    if num_rings%sx == 0: 
        sy = int(num_rings/sx)
    else:
        sy=int(num_rings/sx+1)  
    
    #print (num_rings)    
    if num_rings!=1:
        if RUN_GUI:
            fig=Figure( figsize=(12, 10) )
        else:
            fig = plt.figure(figsize=(12, 10))
        plt.axis('off')
        #plt.axes(frameon=False)    
        plt.xticks([])
        plt.yticks([])       
        
    else:
        if RUN_GUI:
            fig=Figure( figsize=(8,8) )
        else:
            fig = plt.figure(figsize=(8,8))
        #print ('here')
    plt.title('uid=%s'%uid,fontsize=20, y =1.06)        
    for i in range(num_rings):
        ax = fig.add_subplot(sx, sy, i+1 )
        ax.set_ylabel("g4") 
        ax.set_title(" Q= " + '%.5f  '%(q_ring_center[i]) + r'$\AA^{-1}$')
        y=g4[:, i]        
        if logx:
            ax.semilogx(taus, y, '-o', markersize=6)
        else:
            ax.plot(taus, y, '-o', markersize=6)
        if 'ylim' in kwargs:
            ax.set_ylim( kwargs['ylim'])
        elif 'vlim' in kwargs:
            vmin, vmax =kwargs['vlim']
            ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])
        else:
            pass
        if 'xlim' in kwargs:
            ax.set_xlim( kwargs['xlim']) 
    fp = path + 'uid=%s--g4-'%(uid)   + '.png'
    plt.savefig( fp, dpi=fig.dpi)
    fig.set_tight_layout(True)    
    if return_fig:
        return fig             
 
def plot_saxs_two_g2( g2, taus, g2b, tausb,res_pargs=None, return_fig=False, *argv,**kwargs):     
    '''plot g2 results, 
       g2: one-time correlation function from a multi-tau method
       g2b: another g2 from a two-time method
       taus: the time delays        
       kwargs: can contains
           vlim: [vmin,vmax]: for the plot limit of y, the y-limit will be [vmin * min(y), vmx*max(y)]
           ylim/xlim: the limit of y and x
       
       e.g.
       plot_saxs_g2( g2b, taus= np.arange( g2b.shape[0]) *timeperframe, q_ring_center = q_ring_center, vlim=[.99, 1.01] )
           
      ''' 
     
    if res_pargs is not None:
        uid = res_pargs['uid'] 
        path = res_pargs['path'] 
        q_ring_center = res_pargs[ 'q_ring_center']

    else:
        
        if 'uid' in kwargs.keys():
            uid = kwargs['uid'] 
        else:
            uid = 'uid'

        if 'q_ring_center' in kwargs.keys():
            q_ring_center = kwargs[ 'q_ring_center']
        else:
            q_ring_center = np.arange(  g2.shape[1] )

        if 'path' in kwargs.keys():
            path = kwargs['path'] 
        else:
            path = ''      
    num_rings = g2.shape[1]
    sx = int(round(np.sqrt(num_rings)) )
    if num_rings%sx == 0: 
        sy = int(num_rings/sx)
    else:
        sy=int(num_rings/sx+1)        
    uid = 'uid'
    if 'uid' in kwargs.keys():
        uid = kwargs['uid']  
    sx = int(round(np.sqrt(num_rings)) )
    if num_rings%sx == 0: 
        sy = int(num_rings/sx)
    else:
        sy=int(num_rings/sx+1)        
    if num_rings!=1:        
        #fig = plt.figure(figsize=(14, 10))
        if RUN_GUI:
            fig = Figure(figsize=(12, 10))
        else:
            fig = plt.figure(figsize=(12, 10))
            #fig = Figure()
        plt.axis('off')
        #plt.axes(frameon=False)
        #print ('here')
        plt.xticks([])
        plt.yticks([])        
    else:
        if RUN_GUI:
            fig = Figure( figsize=(8,8) )
        else:
            fig = plt.figure(figsize=(8,8))
    plt.title('uid=%s'%uid,fontsize=20, y =1.06)  
    plt.axis('off')
    for sn in range(num_rings):
        ax = fig.add_subplot(sx,sy,sn+1 )
        ax.set_ylabel("g2") 
        ax.set_title(" Q= " + '%.5f  '%(q_ring_center[sn]) + r'$\AA^{-1}$')     
        y=g2b[:, sn]
        ax.semilogx( tausb, y, '--rs', markersize=6,label= 'from_two-time')  

        y2=g2[:, sn]
        ax.semilogx(taus, y2, '--bo', markersize=6,  label= 'from_one_time') 
        if 'ylim' in kwargs:
            ax.set_ylim( kwargs['ylim'])
        elif 'vlim' in kwargs:
            vmin, vmax =kwargs['vlim']
            ax.set_ylim([min(y2)*vmin, max(y2[1:])*vmax ])
        else:
            pass
        if 'xlim' in kwargs:
            ax.set_xlim( kwargs['xlim'])        
        if sn==0:
            ax.legend(loc = 'best') 

    #dt =datetime.now()
    #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)        
    fig.set_tight_layout(True)       
    #fp = path + 'g2--uid=%s'%(uid) + CurTime + '--twog2.png'
    fp = path + 'uid=%s--g2'%(uid) + '--two-g2-.png'
    plt.savefig( fp, dpi=fig.dpi)        
    if return_fig:
        return fig
    
    
#plot g2 results
def plot_saxs_rad_ang_g2( g2, taus, res_pargs=None, master_angle_plot= False,return_fig=False,*argv,**kwargs):     
    '''plot g2 results of segments with radius and angle partation , 
    
       g2: one-time correlation function
       taus: the time delays  
       res_pargs, a dict, can contains
           uid/path/qr_center/qz_center/
       master_angle_plot: if True, plot angle first, then q
       kwargs: can contains
           vlim: [vmin,vmax]: for the plot limit of y, the y-limit will be [vmin * min(y), vmx*max(y)]
           ylim/xlim: the limit of y and x
       
       e.g.
       plot_saxs_rad_ang_g2( g2b, taus= np.arange( g2b.shape[0]) *timeperframe, q_ring_center = q_ring_center, ang_center=ang_center, vlim=[.99, 1.01] )
           
      '''     
    if res_pargs is not None:
        uid = res_pargs['uid'] 
        path = res_pargs['path'] 
        q_ring_center= res_pargs[ 'q_ring_center']
        num_qr = len( q_ring_center)
        ang_center = res_pargs[ 'ang_center']
        num_qa = len( ang_center )
    
    else:
    
        if 'uid' in kwargs.keys():
            uid = kwargs['uid'] 
        else:
            uid = 'uid'
        if 'path' in kwargs.keys():
            path = kwargs['path'] 
        else:
            path = ''
        if 'q_ring_center' in kwargs.keys():
            q_ring_center = kwargs[ 'q_ring_center']
            num_qr = len( q_ring_center)
        else:
            print( 'Please give q_ring_center')
        if 'ang_center' in kwargs.keys():
            ang_center = kwargs[ 'ang_center']
            num_qa = len( ang_center)
        else:
            print( 'Please give ang_center') 
        
    if master_angle_plot:
        first_var = num_qa
        sec_var = num_qr
    else:
        first_var=num_qr
        sec_var = num_qa
        
    for qr_ind in range( first_var  ):
        if RUN_GUI:
            fig = Figure(figsize=(10, 12))            
        else:
            fig = plt.figure(figsize=(10, 12)) 
        #fig = plt.figure()
        if master_angle_plot:
            title_qr = 'Angle= %.2f'%( ang_center[qr_ind]) + r'$^\circ$' 
        else:
            title_qr = ' Qr= %.5f  '%( q_ring_center[qr_ind]) + r'$\AA^{-1}$' 
        
        plt.title('uid= %s:--->'%uid + title_qr,fontsize=20, y =1.1) 
        #print (qz_ind,title_qz)
        #if num_qr!=1:plt.axis('off')
        plt.axis('off')    
        sx = int(round(np.sqrt(  sec_var  )) )
        if sec_var%sx == 0: 
            sy = int(sec_var/sx)
        else: 
            sy=int(sec_var/sx+1) 
            
        for sn in range( sec_var ):
            ax = fig.add_subplot(sx,sy,sn+1 )
            ax.set_ylabel("g2") 
            ax.set_xlabel(r"$\tau $ $(s)$", fontsize=16) 
            if master_angle_plot:
                i = sn + qr_ind * num_qr
                title_qa =  '%.5f  '%( q_ring_center[sn]) + r'$\AA^{-1}$' 
            else:
                i = sn + qr_ind * num_qa
                title_qa = '%.2f'%( ang_center[sn]) + r'$^\circ$' + '( %d )'%(i)
            #title_qa = " Angle= " + '%.2f'%( ang_center[sn]) + r'$^\circ$' + '( %d )'%i
            
            #title_qa = '%.2f'%( ang_center[sn]) + r'$^\circ$' + '( %d )'%(i)
            #if num_qr==1:
            #    title = 'uid= %s:--->'%uid + title_qr + '__' +  title_qa
            #else:
            #    title = title_qa
            title = title_qa
            ax.set_title( title , y =1.1, fontsize=12)             
            y=g2[:, i]
            ax.semilogx(taus, y, '-o', markersize=6)             
            
            if 'ylim' in kwargs:
                ax.set_ylim( kwargs['ylim'])
            elif 'vlim' in kwargs:
                vmin, vmax =kwargs['vlim']
                ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])                
            else:
                pass
            
            if 'xlim' in kwargs:
                ax.set_xlim( kwargs['xlim'])

        #dt =datetime.now()
        #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)        
                
        #fp = path + 'g2--uid=%s-qr=%s'%(uid,q_ring_center[qr_ind]) + CurTime + '.png'         
        fp = path + 'uid=%s--g2-qr=%s'%(uid, q_ring_center[qr_ind] )  + '-.png'
        plt.savefig( fp, dpi=fig.dpi)        
        fig.set_tight_layout(True)        
    if return_fig:
        return fig


    
###########
#*for g2 fit and plot

def stretched_auto_corr_scat_factor(x, beta, relaxation_rate, alpha=1.0, baseline=1):
    return beta * (np.exp(-2 * relaxation_rate * x))**alpha + baseline

def simple_exponential(x, beta, relaxation_rate,  baseline=1):
    return beta * np.exp(-2 * relaxation_rate * x) + baseline


def simple_exponential_with_vibration(x, beta, relaxation_rate, freq, amp,  baseline=1):
    return beta * (1 + amp*np.cos(  2*np.pi*freq* x) )* np.exp(-2 * relaxation_rate * x) + baseline

def stretched_auto_corr_scat_factor_with_vibration(x, beta, relaxation_rate, alpha, freq, amp,  baseline=1):
    return beta * (1 + amp*np.cos(  2*np.pi*freq* x) )* np.exp(-2 * relaxation_rate * x)**alpha + baseline


def flow_para_function_with_vibration( x, beta, relaxation_rate, flow_velocity, freq, amp, baseline=1): 
    
    vibration_part = (1 + amp*np.cos(  2*np.pi*freq* x) )    
    Diff_part=    np.exp(-2 * relaxation_rate * x)
    Flow_part =  np.pi**2/(16*x*flow_velocity) *  abs(  erf(  np.sqrt(   4/np.pi * 1j* x * flow_velocity ) ) )**2  
    
    return  beta* vibration_part* Diff_part * Flow_part + baseline


def flow_para_function( x, beta, relaxation_rate, flow_velocity, baseline=1):    
    Diff_part=    np.exp(-2 * relaxation_rate * x)
    Flow_part =  np.pi**2/(16*x*flow_velocity) *  abs(  erf(  np.sqrt(   4/np.pi * 1j* x * flow_velocity ) ) )**2    
    return  beta*Diff_part * Flow_part + baseline


def get_flow_velocity( average_velocity, shape_factor):    
    return average_velocity * (1- shape_factor)/(1+  shape_factor)


    
############################################
##a good func to save g2 for all types of geogmetries
############################################ 

def save_g2(  g2, taus, qr=None, qz=None, uid='uid', path=None ):
    
    '''save g2 results, 
       res_pargs should contain
           g2: one-time correlation function
           taus, lags of g2
           qr: the qr center, same length as g2
           qz: the qz or angle center, same length as g2
           path:
           uid:
      
      '''    
    
    df = DataFrame(     np.hstack( [ (taus).reshape( len(g2),1) ,  g2] )  ) 
    t,qs = g2.shape
    if qr is None:
        qr = range( qs )
    if qz is None:        
        df.columns = (   ['tau'] + [str(qr_)  for qr_ in qr ]    )
    else:
        df.columns = (   ['tau'] + [ str(qr_) + str(qz_)  for (qr_,qz_) in zip(qr,qz) ]    )
    
    #dt =datetime.now()
    #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)  
    
    #if filename is None:
    filename = 'uid=%s--g2.csv' % (uid)
    #filename += '-uid=%s-%s.csv' % (uid,CurTime)   
    #filename += '-uid=%s.csv' % (uid) 
    filename1 = os.path.join(path, filename)
    df.to_csv(filename1)
    print( 'The correlation function is saved in %s with filename as %s'%( path, filename))



############################################
##a good func to fit g2 for all types of geogmetries
############################################ 



def get_g2_fit( g2, res_pargs=None, function='simple_exponential', *argv,**kwargs):
    '''
    Aug 5,2016, Y.G.@CHX
    
    Fit one-time correlation function
    
    The support functions include simple exponential and stretched/compressed exponential
    Parameters
    ---------- 
    g2: one-time correlation function for fit, with shape as [taus, qs]
    res_pargs: a dict, contains keys
        taus: the time delay, with the same length as g2
        q_ring_center:  the center of q rings, for the title of each sub-plot
        uid: unique id, for the title of plot
        
    function: 
        'simple_exponential': fit by a simple exponential function, defined as  
                    beta * np.exp(-2 * relaxation_rate * lags) + baseline
        'streched_exponential': fit by a streched exponential function, defined as  
                    beta * (np.exp(-2 * relaxation_rate * lags))**alpha + baseline
                    
         'stretched_vibration': fit by a streched exponential function with vibration, defined as            
                 beta * (1 + amp*np.cos(  2*np.pi*60* x) )* np.exp(-2 * relaxation_rate * x)**alpha + baseline
         'flow_para_function': fit by a flow function
         
                    
    kwargs:
        could contains:
            'fit_variables': a dict, for vary or not, 
                                keys are fitting para, including 
                                    beta, relaxation_rate , alpha ,baseline
                                values: a False or True, False for not vary
            'guess_values': a dict, for initial value of the fitting para,
                            the defalut values are 
                                dict( beta=.1, alpha=1.0, relaxation_rate =0.005, baseline=1.0)
                    
    Returns
    -------        
    fit resutls: a instance in limfit
    fit_data by the model, it has the q number of g2
         
    an example:
        result,fd = fit_g2( g2, res_pargs, function = 'simple')
        result,fd = fit_g2( g2, res_pargs, function = 'stretched')
    '''      
    
    if 'fit_range' in kwargs.keys():
        fit_range = kwargs['fit_range'] 
    else:
        fit_range=None    

    if res_pargs is not None:
        taus = res_pargs[ 'taus']
    else:
        taus =  kwargs['taus'] 
    num_rings = g2.shape[1]    
    if 'fit_variables' in kwargs:
        additional_var  = kwargs['fit_variables']        
        _vars =[ k for k in list( additional_var.keys()) if additional_var[k] is False]
    else:
        _vars = []        
    if function=='simple_exponential' or function=='simple':
        _vars = np.unique ( _vars + ['alpha']) 
        mod = Model(stretched_auto_corr_scat_factor)#,  independent_vars= list( _vars)   )        
    elif function=='stretched_exponential' or function=='stretched':        
        mod = Model(stretched_auto_corr_scat_factor)#,  independent_vars=  _vars)       
    elif function=='stretched_vibration':        
        mod = Model(stretched_auto_corr_scat_factor_with_vibration)#,  independent_vars=  _vars)        
    elif function=='flow_para_function' or  function=='flow_para':         
        mod = Model(flow_para_function)#,  independent_vars=  _vars) 
    elif function=='flow_para_function_with_vibration' or  function=='flow_vibration':            
        mod = Model( flow_para_function_with_vibration )
        
    else:
        print ("The %s is not supported.The supported functions include simple_exponential and stretched_exponential"%function)
        
    mod.set_param_hint( 'baseline',   min=0.5, max= 2.5 )
    mod.set_param_hint( 'beta',   min=0.0,  max=1.0 )
    mod.set_param_hint( 'alpha',   min=0.0 )
    mod.set_param_hint( 'relaxation_rate',   min=0.0,  max= 1000  )  
    
    if function=='flow_para_function' or  function=='flow_para' or function=='flow_vibration': 
        mod.set_param_hint( 'flow_velocity', min=0)        
    if function=='stretched_vibration' or function=='flow_vibration':     
        mod.set_param_hint( 'freq', min=0)
        mod.set_param_hint( 'amp', min=0)
        
    _guess_val = dict( beta=.1, alpha=1.0, relaxation_rate =0.005, baseline=1.0)    
    if 'guess_values' in kwargs:         
        guess_values  = kwargs['guess_values']         
        _guess_val.update( guess_values )  
   
    _beta=_guess_val['beta']
    _alpha=_guess_val['alpha']
    _relaxation_rate = _guess_val['relaxation_rate']
    _baseline= _guess_val['baseline']    
    pars  = mod.make_params( beta=_beta, alpha=_alpha, relaxation_rate =_relaxation_rate, baseline= _baseline)
    if function=='flow_para_function' or  function=='flow_para':
        _flow_velocity =_guess_val['flow_velocity']    
        pars  = mod.make_params( beta=_beta, alpha=_alpha, flow_velocity=_flow_velocity,
                                relaxation_rate =_relaxation_rate, baseline= _baseline)
        
    if function=='stretched_vibration':
        _freq =_guess_val['freq'] 
        _amp = _guess_val['amp'] 
        pars  = mod.make_params( beta=_beta, alpha=_alpha, freq=_freq, amp = _amp,
                                relaxation_rate =_relaxation_rate, baseline= _baseline)
        
    if  function=='flow_vibration':
        _flow_velocity =_guess_val['flow_velocity']    
        _freq =_guess_val['freq'] 
        _amp = _guess_val['amp'] 
        pars  = mod.make_params( beta=_beta,  freq=_freq, amp = _amp,flow_velocity=_flow_velocity,
                                relaxation_rate =_relaxation_rate, baseline= _baseline)        
        
    for v in _vars:
        pars['%s'%v].vary = False
    #print( pars )
    fit_res = []
    model_data = []    
    for i in range(num_rings):  
        if fit_range is not None:
            y=g2[1:, i][fit_range[0]:fit_range[1]]
            lags=taus[1:][fit_range[0]:fit_range[1]] 
        else:
            y=g2[1:, i]
            lags=taus[1:]            
        result1 = mod.fit(y, pars, x =lags )        
        fit_res.append( result1) 
        model_data.append(  result1.best_fit )
        
        #print(  result1.best_values['freq'] )
        
    return fit_res, lags, np.array( model_data ).T




############################################
##a good func to plot g2 for all types of geogmetries
############################################ 

        


def plot_g2( g2, res_pargs, tau_2=None, g2_2=None, fit_res=None,  geometry='saxs', function='simple_exponential', 
            master_plot=None, one_plot= True, plot_g1=False,return_fig=False, *argv,**kwargs):    
    '''
    Octo 8,2016, Y.G.@CHX
    
    Plot one-time correlation function (with fit) for different geometry
    
    The support functions include simple exponential and stretched/compressed exponential
    Parameters
    ---------- 
    g2: one-time correlation function for fit, with shape as [taus, qs]
    tau_2: if not None, will plot g2 with g2_fit using tau_fit as x
    g2_2: if not None, will plot g2 with the g2_fit
    fit_res: give all the fitting parameters for showing in the plot
    
    res_pargs: a dict, contains keys
        taus: the time delay, with the same length as g2
        q_ring_center:  the center of q rings, for the title of each sub-plot
        uid: unique id, for the title of plot  
        path: the path to save data        
        
    function: 
        'simple_exponential': fit by a simple exponential function, defined as  
                    beta * np.exp(-2 * relaxation_rate * lags) + baseline
        'streched_exponential': fit by a streched exponential function, defined as  
                    beta * (np.exp(-2 * relaxation_rate * lags))**alpha + baseline  
    geometry:
        'saxs':  a saxs with Qr partition
        'ang_saxs': a saxs with Qr and angular partition
        'gi_saxs': gisaxs with Qz, Qr
        
    master_plot:  can support 'angle' or 'qr' for saxs
                               'qz' or 'qr' for gisaxs
                  if not None, 
                  take master_plot = 'angle' for example, it will plot the different qr for one angle
    one_plot: if True, plot all images in one pannel 
    kwargs:
                    
    Returns
    -------        
    the plot

    '''
    
    uid = res_pargs['uid'] 
    path = res_pargs['path'] 
    taus = res_pargs[ 'taus']
    ##for saxs
    if 'q_ring_center' in res_pargs.keys(): 
        qr_center = res_pargs[ 'q_ring_center']
        num_qr = len( qr_center)
    elif 'qr_center' in res_pargs.keys():          
        qr_center = res_pargs[ 'qr_center']
        num_qr = len( qr_center)  
    else:
        print( 'please give qr center')
    #for ang_saxs
    if 'ang_center' in res_pargs.keys():        
        #ang_center = res_pargs[ 'ang_center']
        #num_qa = len( ang_center )         
        qz_center = res_pargs[ 'ang_center']
        num_qz = len( qz_center)           
    #for gi_saxs        
    elif 'qz_center' in res_pargs.keys():         
        qz_center = res_pargs[ 'qz_center']
        num_qz = len( qz_center)
    else:
        num_qz = 1   #for simple saxs     
        
    if one_plot:       
        
        if master_plot == 'qz' or master_plot == 'angle':
            first_var = num_qz
            sec_var = num_qr
        else:
            first_var=num_qr
            sec_var = num_qz  
            
        for qr_ind in range( first_var  ):
            if RUN_GUI:
                fig = Figure(figsize=(10, 12))            
            else:
                fig = plt.figure(figsize=(10, 12)) 
            #fig = plt.figure()
            
            if master_plot == 'qz' or master_plot == 'angle':
                if geometry=='ang_saxs':
                    title_qr = 'Angle= %.2f'%( qz_center[qr_ind]) + r'$^\circ$' 
                    filename = 'Angle= %.2f'%( qz_center[qr_ind])
                elif geometry=='gi_saxs':
                    title_qr = 'Qz= %.2f'%( qz_center[qr_ind]) + r'$\AA^{-1}$' 
                    filename = 'Qz= %.2f'%( qz_center[qr_ind])
                else:
                    title_qr = ''
                    filename=''
            else: #qr
                if geometry=='ang_saxs' or geometry=='gi_saxs':
                    title_qr = 'Qr= %.5f  '%( qr_center[qr_ind]) + r'$\AA^{-1}$' 
                    filename='Qr= %.5f  '%( qr_center[qr_ind])
                else:
                    title_qr=''
                    filename=''

            plt.title('uid= %s:--->'%uid + title_qr,fontsize=20, y =1.06) 
            #print (qz_ind,title_qz)
            #if num_qr!=1:plt.axis('off')
            if sec_var!=1:            
                plt.axis('off')                 
            sx = int(round(np.sqrt(  sec_var  )) )
            
            if sec_var%sx == 0: 
                sy = int(sec_var/sx)
            else: 
                sy=int(sec_var/sx+1)             
            
            for sn in range( sec_var ):
                ax = fig.add_subplot(sx,sy,sn+1 )
                ax.set_ylabel( r"$g_2$" + '(' + r'$\tau$' + ')' ) 
                ax.set_xlabel(r"$\tau $ $(s)$", fontsize=16) 
                if master_plot == 'qz' or master_plot == 'angle':
                    i = sn + qr_ind * num_qr       
                    if geometry=='ang_saxs' or  geometry=='gi_saxs' or geometry=='saxs':                                      
                        title_qz =  r'$Q_r= $'+'%.5f  '%( qr_center[sn]) + r'$\AA^{-1}$'                    
                else: #if the first one is qr
                    i = sn + qr_ind * num_qz
                    if geometry=='ang_saxs':
                        title_qz = 'Ang= ' + '%.2f'%( qz_center[sn]) + r'$^\circ$' + '( %d )'%(i)
                    elif geometry=='gi_saxs':
                        title_qz =   r'$Q_z= $'+ '%.5f  '%( qz_center[sn]) + r'$\AA^{-1}$'  
                    else:
                        title_qz = ''                        

                title = title_qz
                ax.set_title( title , y =1.1, fontsize=12) 
                
                y=g2[:, i]
                ax.semilogx(taus, y, '-o', markersize=6)   
                
                if g2_2 is not None:                    
                    y=g2_2[:, i]
                    ax.semilogx( tau_2, y, '-r', markersize=6)                    
                    
 
                if fit_res is not None:
                    result1 = fit_res[i]    
                    #print (result1.best_values)
                    rate = result1.best_values['relaxation_rate']
                    beta = result1.best_values['beta'] 
                    baseline =  result1.best_values['baseline'] 
                    if function=='simple_exponential' or function=='simple':
                        alpha =1.0 
                    elif function=='stretched_exponential' or function=='stretched':
                        alpha = result1.best_values['alpha']
                    elif function=='stretched_vibration': 
                        alpha = result1.best_values['alpha']
                        freq = result1.best_values['freq'] 
                    elif function=='flow_vibration': 
                        freq = result1.best_values['freq'] 
                    if function=='flow_para_function' or  function=='flow_para' or  function=='flow_vibration': 
                        flow = result1.best_values['flow_velocity']                          

                    txts = r'$\gamma$' + r'$ = %.3f$'%(1/rate) +  r'$ s$'
                    x=0.25
                    y0=0.9
                    fontsize = 12
                    
                    
                    #print( 'gamma here')
                    #print (sn,i)
                    
                    
                    ax.text(x =x, y= y0, s=txts, fontsize=fontsize, transform=ax.transAxes) 
                    #print(function)
                    dt=0
                    if function!='flow_para_function' and  function!='flow_para' and function!='flow_vibration':
                        txts = r'$\alpha$' + r'$ = %.3f$'%(alpha)  
                        dt +=0.1
                        #txts = r'$\beta$' + r'$ = %.3f$'%(beta[i]) +  r'$ s^{-1}$'
                        ax.text(x =x, y= y0-dt, s=txts, fontsize=fontsize, transform=ax.transAxes) 
                    txts = r'$baseline$' + r'$ = %.3f$'%( baseline) 
                    dt +=0.1
                    ax.text(x =x, y= y0- dt, s=txts, fontsize=fontsize, transform=ax.transAxes) 
                    if function=='flow_para_function' or  function=='flow_para' or  function=='flow_vibration': 
                        txts = r'$flow_v$' + r'$ = %.3f$'%( flow) 
                        dt += 0.1
                        ax.text(x =x, y= y0- dt, s=txts, fontsize=fontsize, transform=ax.transAxes)                        
                    if function=='stretched_vibration'  or  function=='flow_vibration': 
                        txts = r'$vibration$' + r'$ = %.1f Hz$'%( freq) 
                        dt += 0.1
                        ax.text(x =x, y= y0-dt, s=txts, fontsize=fontsize, transform=ax.transAxes)               
                    
                
                if 'ylim' in kwargs:
                    ax.set_ylim( kwargs['ylim'])
                elif 'vlim' in kwargs:
                    vmin, vmax =kwargs['vlim']
                    ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])                
                else:
                    pass
                if 'xlim' in kwargs:
                    ax.set_xlim( kwargs['xlim'])              
            if sn ==0:
                ax.legend(loc='best', fontsize = 6)
                
        file_name =   'uid=%s--g2-%s'%(uid, filename)
        fp = path + file_name  + '-.png'
        plt.savefig( fp, dpi=fig.dpi)        
        fig.set_tight_layout(True)        
    if return_fig:
        return fig               

        
        
def plot_g2_not_work( g2, taus,  qr=None, qz=None, uid='uid', path=None, 
            tau_2=None, g2_2=None, fit_res=None,  geometry='saxs', function='simple_exponential', 
            one_plot=False,
             return_fig=False, *argv,**kwargs):    
    '''
    Octo 18,2016, Y.G.@CHX
    
    Plot one-time correlation function (with fit) for different geometry
    
    The support functions include simple exponential and stretched/compressed exponential
    Parameters
    ---------- 
    g2: one-time correlation function [taus, qs]
    taus, taus for g2
    qr: the qr center, same length as g2
    qz: the qz or angle center, same length as g2
    path: the path for save
    uid:   uid, or filename
    
    tau_2: if not None, will plot g2 with g2_fit using tau_fit as x
    g2_2: if not None, will plot g2 with the g2_fit
    fit_res: give all the fitting parameters for showing in the plot    
    
        
    function: 
        'simple_exponential': fit by a simple exponential function, defined as  
                    beta * np.exp(-2 * relaxation_rate * lags) + baseline
        'streched_exponential': fit by a streched exponential function, defined as  
                    beta * (np.exp(-2 * relaxation_rate * lags))**alpha + baseline  
    geometry:
        'saxs':  a saxs with Qr partition
        'ang_saxs': a saxs with Qr and angular partition
        'gi_saxs': gisaxs with Qz, Qr
        
    master_plot:  can support 'angle' or 'qr' for saxs
                               'qz' or 'qr' for gisaxs
                  if not None, 
                  take master_plot = 'angle' for example, it will plot the different qr for one angle
    
    kwargs:
                    
    Returns
    -------        
    the plot

    '''
    
    t,qs = g2.shape
    if qr is None:
        qr = range( qs )
    num_qr = len(  np.unique(qr) )
    N = len(qr)
    qr_center = qr
    
    if qz is None:
        num_qz = 0   
    else:
        qz_center = qz
        num_qz = len(  np.unique(qz) )
    
    sx = int(round(np.sqrt(  N )) )
    sx=4
    if N%sx == 0: 
        sy = int(N/sx)
    else: 
        sy=int(N/sx+1)  
    if sy%4==0:   
        Nplt = sy//4
    else:
        Nplt= sy//4+1
        
    for ny in range(Nplt): 
        N1, N2 = ny*16, (ny+1)*16
        fig, axs = plt.subplots(sy,sx, figsize=(10, 12))
        aX,aY = axs.shape
        for sn in range(N1,N2):         
            ax = axs[sn//aY, sn%aY]    
            ax.set_ylabel( r"$g_2$" + '(' + r'$\tau$' + ')' ) 
            ax.set_xlabel(r"$\tau $ $(s)$", fontsize=16)            
            if geometry=='ang_saxs' or  geometry=='gi_saxs' or geometry=='saxs':                                      
                title_qr =  r'$Q_r= $'+'%.5f  '%( qr_center[sn]) + r'$\AA^{-1}$' 
                if num_qz!=0: 
                    if geometry=='ang_saxs':
                        title_qz = 'Ang= ' + '%.2f'%( qz_center[sn]) + r'$^\circ$' + '( %d )'%(sn)
                    elif geometry=='gi_saxs':
                        title_qz =   r'$Q_z= $'+ '%.5f  '%( qz_center[sn]) + r'$\AA^{-1}$'  
                    else:
                        title_qz = ''                        


            ax.set_title( title_qr, y =1.1, fontsize=12) 
            if title_qz!='':
                ax.set_title( title_qz, y =1.05, fontsize=12) 

            y=g2[:, sn]
            ax.semilogx(taus, y, '-o', markersize=6)  
            if g2_2 is not None:                    
                y=g2_2[:, i]
                ax.semilogx( tau_2, y, '-r', markersize=6)  

            if sn ==0:
                ax.legend(loc='best', fontsize = 6)

            if 'ylim' in kwargs:
                ax.set_ylim( kwargs['ylim'])
            elif 'vlim' in kwargs:
                vmin, vmax =kwargs['vlim']
                ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])                
            else:
                pass
            if 'xlim' in kwargs:
                ax.set_xlim( kwargs['xlim'])             


        file_name =   'uid=%s--g2'%(uid)
        fp = path + file_name  + '-.png'
        plt.savefig( fp, dpi=fig.dpi)        
        fig.set_tight_layout(True)    
    
    
    if num_qr>=num_qz:
        master_plot = 'qz'
    else:
        master_plot = 'qr'        
        
    if master_plot == 'qz':
        first_var = num_qz
        sec_var = num_qr
    else:
        first_var=num_qr
        sec_var = num_qz  
        
        
    if not one_plot:        
        for qr_ind in range( 0  ):
            if RUN_GUI:
                fig = Figure(figsize=(10, 12))            
            else:
                fig = plt.figure(figsize=(10, 12)) 
            #fig = plt.figure()

            if master_plot == 'qz':
                if geometry=='ang_saxs':
                    title_qr = 'Angle= %.2f'%( qz_center[qr_ind]) + r'$^\circ$' 
                    filename = 'Angle= %.2f'%( qz_center[qr_ind])
                elif geometry=='gi_saxs':
                    title_qr = 'Qz= %.2f'%( qz_center[qr_ind]) + r'$\AA^{-1}$' 
                    filename = 'Qz= %.2f'%( qz_center[qr_ind])
                else:
                    title_qr = ''
                    filename=''
            else: #qr
                if geometry=='ang_saxs' or geometry=='gi_saxs':
                    title_qr = 'Qr= %.5f  '%( qr_center[qr_ind]) + r'$\AA^{-1}$' 
                    filename='Qr= %.5f  '%( qr_center[qr_ind])
                else:
                    title_qr=''
                    filename=''
            plt.title('uid= %s:--->'%uid + title_qr,fontsize=20, y =1.05) 
            if sec_var!=1:            
                plt.axis('off')         
            sx = int(round(np.sqrt(  sec_var  )) )
            if sec_var%sx == 0: 
                sy = int(sec_var/sx)
            else: 
                sy=int(sec_var/sx+1) 

             
            

def dum():
              
    sx = int(round(np.sqrt(  sec_var  )) )

    if sec_var%sx == 0: 
        sy = int(sec_var/sx)
    else: 
        sy=int(sec_var/sx+1)             

    for sn in range( sec_var ):
        ax = fig.add_subplot(sx,sy,sn+1 )
        ax.set_ylabel( r"$g_2$" + '(' + r'$\tau$' + ')' ) 
        ax.set_xlabel(r"$\tau $ $(s)$", fontsize=16) 
        if master_plot == 'qz' or master_plot == 'angle':
            i = sn + qr_ind * num_qr       
            if geometry=='ang_saxs' or  geometry=='gi_saxs' or geometry=='saxs':                                      
                title_qz =  r'$Q_r= $'+'%.5f  '%( qr_center[sn]) + r'$\AA^{-1}$'                    
        else: #if the first one is qr
            i = sn + qr_ind * num_qz
            if geometry=='ang_saxs':
                title_qz = 'Ang= ' + '%.2f'%( qz_center[sn]) + r'$^\circ$' + '( %d )'%(i)
            elif geometry=='gi_saxs':
                title_qz =   r'$Q_z= $'+ '%.5f  '%( qz_center[sn]) + r'$\AA^{-1}$'  
            else:
                title_qz = ''                        

        title = title_qz
        ax.set_title( title , y =1.1, fontsize=12) 

        y=g2[:, i]
        ax.semilogx(taus, y, '-o', markersize=6)   

        if g2_2 is not None:                    
            y=g2_2[:, i]
            ax.semilogx( tau_2, y, '-r', markersize=6)                    


        if fit_res is not None:
            result1 = fit_res[i]        
            rate = result1.best_values['relaxation_rate']
            beta = result1.best_values['beta'] 
            baseline =  result1.best_values['baseline'] 
            if function=='simple_exponential' or function=='simple':
                alpha =1.0 
            elif function=='stretched_exponential' or function=='stretched':
                alpha = result1.best_values['alpha']
            elif function=='stretched_vibration':
                alpha = result1.best_values['alpha']    
                freq = result1.best_values['freq'] 
            if function=='flow_para_function' or  function=='flow_para':
                flow = result1.best_values['flow_velocity']    

            txts = r'$\gamma$' + r'$ = %.3f$'%(1/rate) +  r'$ s$'
            x=0.25
            y0=0.9
            fontsize = 12
            ax.text(x =x, y= y0, s=txts, fontsize=fontsize, transform=ax.transAxes)     
            txts = r'$\alpha$' + r'$ = %.3f$'%(alpha)  
            #txts = r'$\beta$' + r'$ = %.3f$'%(beta[i]) +  r'$ s^{-1}$'
            ax.text(x =x, y= y0-.1, s=txts, fontsize=fontsize, transform=ax.transAxes) 
            txts = r'$baseline$' + r'$ = %.3f$'%( baseline) 
            ax.text(x =x, y= y0-.2, s=txts, fontsize=fontsize, transform=ax.transAxes) 
            if function=='flow_para_function' or  function=='flow_para':
                txts = r'$flow_v$' + r'$ = %.3f$'%( flow) 
                ax.text(x =x, y= y0-.3, s=txts, fontsize=fontsize, transform=ax.transAxes)                        
            if function=='stretched_vibration':
                txts = r'$vibration$' + r'$ = %.1f Hz$'%( freq) 
                ax.text(x =x, y= y0-.3, s=txts, fontsize=fontsize, transform=ax.transAxes)  




        if 'ylim' in kwargs:
            ax.set_ylim( kwargs['ylim'])
        elif 'vlim' in kwargs:
            vmin, vmax =kwargs['vlim']
            ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])                
        else:
            pass
        if 'xlim' in kwargs:
            ax.set_xlim( kwargs['xlim'])              
    if sn ==0:
        ax.legend(loc='best', fontsize = 6)

    file_name =   'uid=%s--g2-%s'%(uid, filename)
    fp = path + file_name  + '-.png'
    plt.savefig( fp, dpi=fig.dpi)        
    fig.set_tight_layout(True)        
    if return_fig:
        return fig               


        
        
        
        
                
            
def dummy():        

    beta = np.zeros(   num_rings )  #  contrast factor
    rate = np.zeros(   num_rings )  #  relaxation rate
    alpha = np.zeros(   num_rings )  #  alpha
    baseline = np.zeros(   num_rings )  #  baseline

    sx = int( round (np.sqrt(num_rings)) )
    if num_rings%sx==0:
        sy = int(num_rings/sx)
    else:
        sy = int(num_rings/sx+1)
        
        
    if function=='simple_exponential' or function=='simple':
        _vars = np.unique ( _vars + ['alpha']) 
        mod = Model(stretched_auto_corr_scat_factor)#,  independent_vars= list( _vars)   )
        
    elif function=='stretched_exponential' or function=='stretched':        
        mod = Model(stretched_auto_corr_scat_factor)#,  independent_vars=  _vars)  
        
    else:
        print ("The %s is not supported.The supported functions include simple_exponential and stretched_exponential"%function)          
    
    #mod.set_param_hint( 'beta', value = 0.05 )
    #mod.set_param_hint( 'alpha', value = 1.0 )
    #mod.set_param_hint( 'relaxation_rate', value = 0.005 )
    #mod.set_param_hint( 'baseline', value = 1.0, min=0.5, max= 1.5 )
    mod.set_param_hint( 'baseline',   min=0.5, max= 2.5 )
    mod.set_param_hint( 'beta',   min=0.0 )
    mod.set_param_hint( 'alpha',   min=0.0 )
    mod.set_param_hint( 'relaxation_rate',   min=0.0 ) 

    _guess_val = dict( beta=.1, alpha=1.0, relaxation_rate =0.005, baseline=1.0)
    
    if 'guess_values' in kwargs:         
        guess_values  = kwargs['guess_values']         
        _guess_val.update( guess_values )  
   
    _beta=_guess_val['beta']
    _alpha=_guess_val['alpha']
    _relaxation_rate = _guess_val['relaxation_rate']
    _baseline= _guess_val['baseline']
    
    pars  = mod.make_params( beta=_beta, alpha=_alpha, relaxation_rate =_relaxation_rate, baseline= _baseline)    
    for v in _vars:
        pars['%s'%v].vary = False
        
    if plot_g1:  
        ylabel='g1'
    else:
        ylabel='g2'
        
    if not one_plot:
        if num_rings!=1:
            #fig = plt.figure(figsize=(14, 10))
            fig = plt.figure(figsize=(12, 10))
            plt.axis('off')
            #plt.axes(frameon=False)
            #print ('here')
            plt.xticks([])
            plt.yticks([])

        else:
            fig = plt.figure(figsize=(8,8))

        #fig = plt.figure(figsize=(8,8))
        plt.title('uid= %s'%uid,fontsize=20, y =1.06)   

        for i in range(num_rings):
            ax = fig.add_subplot(sx, sy, i+1 )

            if fit_range is not None:
                y=g2[1:, i][fit_range[0]:fit_range[1]]
                lags=taus[1:][fit_range[0]:fit_range[1]]
            else:
                y=g2[1:, i]
                lags=taus[1:]


            result1 = mod.fit(y, pars, x =lags )


            #print ( result1.best_values)
            rate[i] = result1.best_values['relaxation_rate']
            #rate[i] = 1e-16
            beta[i] = result1.best_values['beta'] 

            #baseline[i] = 1.0
            baseline[i] =  result1.best_values['baseline'] 

            if function=='simple_exponential' or function=='simple':
                alpha[i] =1.0 
            elif function=='stretched_exponential' or function=='stretched':
                alpha[i] = result1.best_values['alpha']
                
            if plot_g1:
                ax.semilogx(taus[1:], ( g2[1:, i] - baseline[i] )/beta[i], 'bo')
                ax.semilogx(lags, (result1.best_fit- baseline[i] )/beta[i], '-r')            
            else:
                ax.semilogx(taus[1:], g2[1:, i], 'bo')
                ax.semilogx(lags, result1.best_fit, '-r')

            ax.set_title(" Q= " + '%.5f  '%(q_ring_center[i]) + r'$\AA^{-1}$')  
            #ax.set_ylim([min(y)*.95, max(y[1:]) *1.05])
            #ax.set_ylim([0.9999, max(y[1:]) *1.002])
            txts = r'$\tau$' + r'$ = %.3f$'%(1/rate[i]) +  r'$ s$'
            ax.text(x =0.02, y=.55, s=txts, fontsize=14, transform=ax.transAxes)     
            txts = r'$\alpha$' + r'$ = %.3f$'%(alpha[i])  
            #txts = r'$\beta$' + r'$ = %.3f$'%(beta[i]) +  r'$ s^{-1}$'
            ax.text(x =0.02, y=.45, s=txts, fontsize=14, transform=ax.transAxes)  

            txts = r'$baseline$' + r'$ = %.3f$'%( baseline[i]) 
            ax.text(x =0.02, y=.35, s=txts, fontsize=14, transform=ax.transAxes) 

            txts = r'$\beta$' + r'$ = %.3f$'%(beta[i]) #+  r'$ s^{-1}$'    
            ax.text(x =0.02, y=.25, s=txts, fontsize=14, transform=ax.transAxes) 

            if 'ylim' in kwargs:
                ax.set_ylim( kwargs['ylim'])
            elif 'vlim' in kwargs:
                vmin, vmax =kwargs['vlim']
                ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])
            else:
                ax.set_ylim([min(y)*.95, max(y[1:]) *1.05])
            if 'xlim' in kwargs:
                ax.set_xlim( kwargs['xlim'])

    else:
        fig = plt.figure(figsize=(8,8))
        #fig = plt.figure(figsize=(8,8))
        plt.title('uid= %s'%uid,fontsize=20, y =1.06)   
        ax = fig.add_subplot(111 )
        ax.set_ylabel(ylabel) 
        for i in range(num_rings):
            if fit_range is not None:
                y=g2[1:, i][fit_range[0]:fit_range[1]]
                lags=taus[1:][fit_range[0]:fit_range[1]]
            else:
                y=g2[1:, i]
                lags=taus[1:]
            result1 = mod.fit(y, pars, x =lags )
            #print ( result1.best_values)
            rate[i] = result1.best_values['relaxation_rate']
            #rate[i] = 1e-16
            beta[i] = result1.best_values['beta'] 
            #baseline[i] = 1.0
            baseline[i] =  result1.best_values['baseline'] 

            if function=='simple_exponential' or function=='simple':
                alpha[i] =1.0 
            elif function=='stretched_exponential' or function=='stretched':
                alpha[i] = result1.best_values['alpha']            
           
                
            if plot_g1:
                #print( baseline[i] , beta[i] )
                y= (g2[1:, i] - baseline[i] )/beta[i]
                ax.semilogx(taus[1:], y,
                            next(markers),color=next(colors),
                            label = "Q= " + '%.5f  '%(q_ring_center[i]) + r'$\AA^{-1}$' )
                
                ax.semilogx(lags, (result1.best_fit- baseline[i] )/beta[i], '-',
                            color=next(colors_copy) )            
            else:
                ax.semilogx(taus[1:], g2[1:, i], 
                    next(markers),label = "Q= " + '%.5f  '%(q_ring_center[i]) + r'$\AA^{-1}$' )
                ax.semilogx(lags, result1.best_fit, '-r')             

        if 'ylim' in kwargs:
            ax.set_ylim( kwargs['ylim'])
        elif 'vlim' in kwargs:
            vmin, vmax =kwargs['vlim']
            ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])
        else:
            ax.set_ylim([min(y)*.95, max(y[1:]) *1.05])
        if 'xlim' in kwargs:
            ax.set_xlim( kwargs['xlim'])
                
        plt.legend(loc='best', fontsize=10)
                
    #dt =datetime.now()
    #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)        
         
    #fp = path + 'g2--uid=%s'%(uid) + CurTime + '--Fit.png'
    fp = path + 'uid=%s--%s) '%(uid,ylabel) + '--fit-.png'
    fig.savefig( fp, dpi=fig.dpi)        
    
    fig.tight_layout()       
    plt.show()

    result = dict( beta=beta, rate=rate, alpha=alpha, baseline=baseline )
    
    return result





def fit_saxs_rad_ang_g2( g2,  res_pargs=None,function='simple_exponential', fit_range=None, 
                        master_angle_plot= False, *argv,**kwargs):    
     
    '''
    Fit one-time correlation function
    
    The support functions include simple exponential and stretched/compressed exponential
    Parameters
    ---------- 
    g2: one-time correlation function for fit, with shape as [taus, qs]
    res_pargs: a dict, contains keys
        taus: the time delay, with the same length as g2
        q_ring_center:  the center of q rings, for the title of each sub-plot
        uid: unique id, for the title of plot
        
    function: 
        'simple_exponential': fit by a simple exponential function, defined as  
                    beta * np.exp(-2 * relaxation_rate * lags) + baseline
        'streched_exponential': fit by a streched exponential function, defined as  
                    beta * (np.exp(-2 * relaxation_rate * lags))**alpha + baseline
     
    #fit_vibration:
    #    if True, will fit the g2 by a dumped sin function due to beamline mechnical oscillation
    
    Returns
    -------        
    fit resutls:
        a dict, with keys as 
        'baseline': 
         'beta':
         'relaxation_rate': 
    an example:
        result = fit_g2( g2, res_pargs, function = 'simple')
        result = fit_g2( g2, res_pargs, function = 'stretched')
    '''
  

    if res_pargs is not None:
        uid = res_pargs['uid'] 
        path = res_pargs['path'] 
        q_ring_center= res_pargs[ 'q_ring_center']
        num_qr = len( q_ring_center)
        ang_center = res_pargs[ 'ang_center']
        num_qa = len( ang_center )
        taus=res_pargs['taus']	
    
    else:
    
        if 'uid' in kwargs.keys():
            uid = kwargs['uid'] 
        else:
            uid = 'uid'
        if 'path' in kwargs.keys():
            path = kwargs['path'] 
        else:
            path = ''
        if 'q_ring_center' in kwargs.keys():
            q_ring_center = kwargs[ 'q_ring_center']
            num_qr = len( q_ring_center)
        else:
            print( 'Please give q_ring_center')
        if 'ang_center' in kwargs.keys():
            ang_center = kwargs[ 'ang_center']
            num_qa = len( ang_center)
        else:
            print( 'Please give ang_center') 
  
            


    num_rings = g2.shape[1]
    beta = np.zeros(   num_rings )  #  contrast factor
    rate = np.zeros(   num_rings )  #  relaxation rate
    alpha = np.zeros(   num_rings )  #  alpha
    baseline = np.zeros(   num_rings )  #  baseline 
    freq= np.zeros(   num_rings )  
    
    if function=='flow_para_function' or  function=='flow_para':
        flow= np.zeros(   num_rings )  #  baseline             
    if 'fit_variables' in kwargs:
        additional_var  = kwargs['fit_variables']        
        _vars =[ k for k in list( additional_var.keys()) if additional_var[k] is False]
    else:
        _vars = []
    
    #print (_vars)

    _guess_val = dict( beta=.1, alpha=1.0, relaxation_rate =0.005, baseline=1.0)
    
    if 'guess_values' in kwargs:         
        guess_values  = kwargs['guess_values']         
        _guess_val.update( guess_values )   
    
    if function=='simple_exponential' or function=='simple':
        _vars = np.unique ( _vars + ['alpha']) 
        mod = Model(stretched_auto_corr_scat_factor)#,  independent_vars= list( _vars)   )
        
        
    elif function=='stretched_exponential' or function=='stretched':        
        mod = Model(stretched_auto_corr_scat_factor)#,  independent_vars=  _vars) 
        
    elif function=='stretched_vibration':        
        mod = Model(stretched_auto_corr_scat_factor_with_vibration)#,  independent_vars=  _vars) 
        
    elif function=='flow_para_function' or  function=='flow_para':         
        mod = Model(flow_para_function)#,  independent_vars=  _vars)
        
    else:
        print ("The %s is not supported.The supported functions include simple_exponential and stretched_exponential"%function)

    mod.set_param_hint( 'baseline',   min=0.5, max= 1.5 )
    mod.set_param_hint( 'beta',   min=0.0 )
    mod.set_param_hint( 'alpha',   min=0.0 )
    mod.set_param_hint( 'relaxation_rate',   min=0.0 )
    if function=='flow_para_function' or  function=='flow_para':
        mod.set_param_hint( 'flow_velocity', min=0)
    if function=='stretched_vibration':     
        mod.set_param_hint( 'freq', min=0)
        mod.set_param_hint( 'amp', min=0)
        
    
    _beta=_guess_val['beta']
    _alpha=_guess_val['alpha']
    _relaxation_rate = _guess_val['relaxation_rate']
    _baseline= _guess_val['baseline']
    pars  = mod.make_params( beta=_beta, alpha=_alpha, relaxation_rate =_relaxation_rate, baseline= _baseline)   
    
    
    if function=='flow_para_function' or  function=='flow_para':
        _flow_velocity =_guess_val['flow_velocity']    
        pars  = mod.make_params( beta=_beta, alpha=_alpha, flow_velocity=_flow_velocity,
                                relaxation_rate =_relaxation_rate, baseline= _baseline)
        
    if function=='stretched_vibration':
        _freq =_guess_val['freq'] 
        _amp = _guess_val['amp'] 
        pars  = mod.make_params( beta=_beta, alpha=_alpha, freq=_freq, amp = _amp,
                                relaxation_rate =_relaxation_rate, baseline= _baseline) 
    
    for v in _vars:
        pars['%s'%v].vary = False        
    if master_angle_plot:
        first_var = num_qa
        sec_var = num_qr
    else:
        first_var=num_qr
        sec_var = num_qa
        
    for qr_ind in range( first_var  ):
        #fig = plt.figure(figsize=(10, 12))
        fig = plt.figure(figsize=(14, 8))
        #fig = plt.figure()
        if master_angle_plot:
            title_qr = 'Angle= %.2f'%( ang_center[qr_ind]) + r'$^\circ$' 
        else:
            title_qr = ' Qr= %.5f  '%( q_ring_center[qr_ind]) + r'$\AA^{-1}$' 
        
        #plt.title('uid= %s:--->'%uid + title_qr,fontsize=20, y =1.1)
        plt.axis('off') 
 
        #sx = int(round(np.sqrt(  sec_var  )) )
        sy=4
        #if sec_var%sx == 0: 
        if sec_var%sy == 0:             
            #sy = int(sec_var/sx)
            sx = int(sec_var/sy)
        else: 
            #sy=int(sec_var/sx+1) 
            sx=int(sec_var/sy+1) 
            
        for sn in range( sec_var ):
            ax = fig.add_subplot(sx,sy,sn+1 )
            ax.set_ylabel(r"$g^($" + r'$^2$' + r'$^)$' + r'$(Q,$' + r'$\tau$' +  r'$)$' ) 
            ax.set_xlabel(r"$\tau $ $(s)$", fontsize=16) 
            if master_angle_plot:
                i = sn + qr_ind * num_qr
                title_qa =  '%.5f  '%( q_ring_center[sn]) + r'$\AA^{-1}$' 
            else:
                i = sn + qr_ind * num_qa
                title_qa = '%.2f'%( ang_center[sn]) + r'$^\circ$' + '( %d )'%(i)        
            
            title = title_qa    
            ax.set_title( title , y =1.1) 

            if fit_range is not None:
                y=g2[1:, i][fit_range[0]:fit_range[1]]
                lags=taus[1:][fit_range[0]:fit_range[1]]
            else:
                y=g2[1:, i]
                lags=taus[1:]   
      
            result1 = mod.fit(y, pars, x =lags )


            #print ( result1.best_values)
            rate[i] = result1.best_values['relaxation_rate']
            #rate[i] = 1e-16
            beta[i] = result1.best_values['beta'] 

            #baseline[i] = 1.0
            baseline[i] =  result1.best_values['baseline'] 
            
            #print( result1.best_values['freq']  )
            


            if function=='simple_exponential' or function=='simple':
                alpha[i] =1.0 
            elif function=='stretched_exponential' or function=='stretched':
                alpha[i] = result1.best_values['alpha']
            elif function=='stretched_vibration':
                alpha[i] = result1.best_values['alpha']    
                freq[i] = result1.best_values['freq']     
            
            if function=='flow_para_function' or  function=='flow_para':
                flow[i] = result1.best_values['flow_velocity']

            ax.semilogx(taus[1:], g2[1:, i], 'ro')
            ax.semilogx(lags, result1.best_fit, '-b')
            
            
            txts = r'$\gamma$' + r'$ = %.3f$'%(1/rate[i]) +  r'$ s$'
            x=0.25
            y0=0.75
            fontsize = 12
            ax.text(x =x, y= y0, s=txts, fontsize=fontsize, transform=ax.transAxes)     
            txts = r'$\alpha$' + r'$ = %.3f$'%(alpha[i])  
            #txts = r'$\beta$' + r'$ = %.3f$'%(beta[i]) +  r'$ s^{-1}$'
            ax.text(x =x, y= y0-.1, s=txts, fontsize=fontsize, transform=ax.transAxes)  

            txts = r'$baseline$' + r'$ = %.3f$'%( baseline[i]) 
            ax.text(x =x, y= y0-.2, s=txts, fontsize=fontsize, transform=ax.transAxes)  
            
            if function=='flow_para_function' or  function=='flow_para':
                txts = r'$flow_v$' + r'$ = %.3f$'%( flow[i]) 
                ax.text(x =x, y= y0-.3, s=txts, fontsize=fontsize, transform=ax.transAxes)         
        
            if 'ylim' in kwargs:
                ax.set_ylim( kwargs['ylim'])
            elif 'vlim' in kwargs:
                vmin, vmax =kwargs['vlim']
                ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])
            else:
                pass
            if 'xlim' in kwargs:
                ax.set_xlim( kwargs['xlim'])

        fp = path + 'uid=%s--g2--qr-%s--fit-'%(uid, q_ring_center[qr_ind] )  + '.png'
        fig.savefig( fp, dpi=fig.dpi)        
        fig.tight_layout()  
        plt.show()
        

    result = dict( beta=beta, rate=rate, alpha=alpha, baseline=baseline )
    if function=='flow_para_function' or  function=='flow_para':
        result = dict( beta=beta, rate=rate, alpha=alpha, baseline=baseline, flow_velocity=flow )
    if function=='stretched_vibration':
        result = dict( beta=beta, rate=rate, alpha=alpha, baseline=baseline, freq= freq )        
        
    return result
                


    
    
    
    
    
    
 
def save_seg_saxs_g2(  g2, res_pargs, time_label=True, *argv,**kwargs):     
    
    '''
    Aug 8, 2016, Y.G.@CHX
    save g2 results, 
       res_pargs should contain
           g2: one-time correlation function
           res_pargs: contions taus, q_ring_center values
           path:
           uid:
      
      '''
    taus = res_pargs[ 'taus']
    qz_center= res_pargs[ 'q_ring_center']       
    qr_center = res_pargs[ 'ang_center']
    path = res_pargs['path']
    uid = res_pargs['uid']
    
    df = DataFrame(     np.hstack( [ (taus).reshape( len(g2),1) ,  g2] )  ) 
    columns=[]
    columns.append('tau')
    
    for qz in qz_center:
        for qr in qr_center:
            columns.append( [str(qz),str(qr)] )
            
    df.columns = columns   
    
    if time_label:
        dt =datetime.now()
        CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)  
        filename = os.path.join(path, 'g2-%s-%s.csv' %(uid,CurTime))
    else:
        filename = os.path.join(path, 'uid=%s--g2.csv' % (uid))
    df.to_csv(filename)
    print( 'The g2 of uid= %s is saved with filename as %s'%(uid, filename))

    

def save_saxs_g2(  g2, res_pargs, taus=None, filename=None ):
    
    '''save g2 results, 
       res_pargs should contain
           g2: one-time correlation function
           res_pargs: contions taus, q_ring_center values
           path:
           uid:
      
      '''
    
    
    if taus is None:
        taus = res_pargs[ 'taus']
    q_ring_center = res_pargs['q_ring_center']
    path = res_pargs['path']
    uid = res_pargs['uid']
    
    df = DataFrame(     np.hstack( [ (taus).reshape( len(g2),1) ,  g2] )  ) 
    df.columns = (   ['tau'] + [str(qs) for qs in q_ring_center ]    )
    
    dt =datetime.now()
    CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)  
    
    if filename is None:
          filename = 'uid=%s--g2.csv' % (uid)
    #filename += '-uid=%s-%s.csv' % (uid,CurTime)   
    #filename += '-uid=%s.csv' % (uid) 
    filename1 = os.path.join(path, filename)
    df.to_csv(filename1)
    print( 'The correlation function is saved in %s with filename as %s'%( path, filename))


    
    
    
    


def plot_fit_saxs_g2( g2, fit_res, fit_para_res, res_pargs=None,  return_fig=False,tight=True,*argv,**kwargs):
    
    if res_pargs is not None:
        uid = res_pargs['uid'] 
        path = res_pargs['path'] 
        taus = res_pargs[ 'taus']
        q_ring_center = res_pargs[ 'q_ring_center']
    else:
        taus =  kwargs['taus'] 
        if 'uid' in kwargs.keys():
            uid = kwargs['uid'] 
        else:
            uid = 'uid'
        if 'q_ring_center' in kwargs.keys():
            q_ring_center = kwargs[ 'q_ring_center']
        else:
            q_ring_center = np.arange(  g2.shape[1] )
        if 'path' in kwargs.keys():
            path = kwargs['path'] 
        else:
            path = ''        
    if 'fit_range' in kwargs.keys():
        fit_range = kwargs['fit_range'] 
    else:
        fit_range=None
    num_rings = g2.shape[1]
    
    beta = fit_para_res['beta'] 
    rate = fit_para_res['rate']
    alpha =  fit_para_res['alpha']
    baseline = fit_para_res['baseline']
    
    sx = int( round (np.sqrt(num_rings)) )
    if num_rings%sx==0:
        sy = int(num_rings/sx)
    else:
        sy = int(num_rings/sx+1)  
    if num_rings!=1:  
        fig = Figure()
        plt.axis('off')
        plt.xticks([])
        plt.yticks([])        
    else:
        fig = Figure()  
    plt.title('uid= %s'%uid,fontsize=20, y =1.06)   
 
    for i in range(num_rings):
        ax = fig.add_subplot(sx, sy, i+1 )        
        if fit_range is not None:
            y=g2[1:, i][fit_range[0]:fit_range[1]]
            lags=taus[1:][fit_range[0]:fit_range[1]]
        else:
            y=g2[1:, i]
            lags=taus[1:]        
        result1 = fit_res[i]  
        ax.semilogx(taus[1:], g2[1:, i], 'bo')        
        ax.semilogx(lags, result1.best_fit, '-r')        
        ax.set_title(" Q= " + '%.5f  '%(q_ring_center[i]) + r'$\AA^{-1}$')  
        #ax.set_ylim([min(y)*.95, max(y[1:]) *1.05])
        #ax.set_ylim([0.9999, max(y[1:]) *1.002])
        txts = r'$\tau$' + r'$ = %.3f$'%(1/rate[i]) +  r'$ s$'
        ax.text(x =0.02, y=.55, s=txts, fontsize=14, transform=ax.transAxes)     
        txts = r'$\alpha$' + r'$ = %.3f$'%(alpha[i])  
        #txts = r'$\beta$' + r'$ = %.3f$'%(beta[i]) +  r'$ s^{-1}$'
        ax.text(x =0.02, y=.45, s=txts, fontsize=14, transform=ax.transAxes) 

        txts = r'$baseline$' + r'$ = %.3f$'%( baseline[i]) 
        ax.text(x =0.02, y=.35, s=txts, fontsize=14, transform=ax.transAxes) 
        
        txts = r'$\beta$' + r'$ = %.3f$'%(beta[i]) #+  r'$ s^{-1}$'    
        ax.text(x =0.02, y=.25, s=txts, fontsize=14, transform=ax.transAxes) 
    
        if 'ylim' in kwargs:
            ax.set_ylim( kwargs['ylim'])
        elif 'vlim' in kwargs:
            vmin, vmax =kwargs['vlim']
            ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])
        else:
            ax.set_ylim([min(y)*.95, max(y[1:]) *1.05])
        if 'xlim' in kwargs:
            ax.set_xlim( kwargs['xlim'])
    fp = path + 'uid=%s--g2'%(uid) + '--fit-.png'
    if tight:
        fig.set_tight_layout(True)
    plt.savefig( fp, dpi=fig.dpi)     
    result = dict( beta=beta, rate=rate, alpha=alpha, baseline=baseline )
    if return_fig:
        return fig    
    
    


def fit_saxs_g2( g2, res_pargs=None, function='simple_exponential',  
                one_plot=False, plot_g1=False, *argv,**kwargs):    
    '''
    Aug 5,2016, Y.G.@CHX
    
    Fit one-time correlation function
    
    The support functions include simple exponential and stretched/compressed exponential
    Parameters
    ---------- 
    g2: one-time correlation function for fit, with shape as [taus, qs]
    res_pargs: a dict, contains keys
        taus: the time delay, with the same length as g2
        q_ring_center:  the center of q rings, for the title of each sub-plot
        uid: unique id, for the title of plot
        
    function: 
        'simple_exponential': fit by a simple exponential function, defined as  
                    beta * np.exp(-2 * relaxation_rate * lags) + baseline
        'streched_exponential': fit by a streched exponential function, defined as  
                    beta * (np.exp(-2 * relaxation_rate * lags))**alpha + baseline
    kwargs:
        could contains:
            'fit_variables': a dict, for vary or not, 
                                keys are fitting para, including 
                                    beta, relaxation_rate , alpha ,baseline
                                values: a False or True, False for not vary
            'guess_values': a dict, for initial value of the fitting para,
                            the defalut values are 
                                dict( beta=.1, alpha=1.0, relaxation_rate =0.005, baseline=1.0)
                    
    Returns
    -------        
    fit resutls:
        a dict, with keys as 
        'baseline': 
         'beta':
         'relaxation_rate': 
    an example:
        result = fit_g2( g2, res_pargs, function = 'simple')
        result = fit_g2( g2, res_pargs, function = 'stretched')
    '''
    
    if res_pargs is not None:
        uid = res_pargs['uid'] 
        path = res_pargs['path'] 
        taus = res_pargs[ 'taus']
        q_ring_center = res_pargs[ 'q_ring_center']

    else:
        taus =  kwargs['taus'] 
        if 'uid' in kwargs.keys():
            uid = kwargs['uid'] 
        else:
            uid = 'uid'

        if 'q_ring_center' in kwargs.keys():
            q_ring_center = kwargs[ 'q_ring_center']
        else:
            q_ring_center = np.arange(  g2.shape[1] )

        if 'path' in kwargs.keys():
            path = kwargs['path'] 
        else:
            path = ''
        
    if 'fit_range' in kwargs.keys():
        fit_range = kwargs['fit_range'] 
    else:
        fit_range=None
 
    
    num_rings = g2.shape[1]
    

    beta = np.zeros(   num_rings )  #  contrast factor
    rate = np.zeros(   num_rings )  #  relaxation rate
    alpha = np.zeros(   num_rings )  #  alpha
    baseline = np.zeros(   num_rings )  #  baseline

    sx = int( round (np.sqrt(num_rings)) )
    if num_rings%sx==0:
        sy = int(num_rings/sx)
    else:
        sy = int(num_rings/sx+1)
        

    if 'fit_variables' in kwargs:
        additional_var  = kwargs['fit_variables']        
        _vars =[ k for k in list( additional_var.keys()) if additional_var[k] is False]
    else:
        _vars = []
        
    if function=='simple_exponential' or function=='simple':
        _vars = np.unique ( _vars + ['alpha']) 
        mod = Model(stretched_auto_corr_scat_factor)#,  independent_vars= list( _vars)   )
        
    elif function=='stretched_exponential' or function=='stretched':        
        mod = Model(stretched_auto_corr_scat_factor)#,  independent_vars=  _vars)  
        
    else:
        print ("The %s is not supported.The supported functions include simple_exponential and stretched_exponential"%function)          
    
    #mod.set_param_hint( 'beta', value = 0.05 )
    #mod.set_param_hint( 'alpha', value = 1.0 )
    #mod.set_param_hint( 'relaxation_rate', value = 0.005 )
    #mod.set_param_hint( 'baseline', value = 1.0, min=0.5, max= 1.5 )
    mod.set_param_hint( 'baseline',   min=0.5, max= 2.5 )
    mod.set_param_hint( 'beta',   min=0.0 )
    mod.set_param_hint( 'alpha',   min=0.0 )
    mod.set_param_hint( 'relaxation_rate',   min=0.0 ) 

    _guess_val = dict( beta=.1, alpha=1.0, relaxation_rate =0.005, baseline=1.0)
    
    if 'guess_values' in kwargs:         
        guess_values  = kwargs['guess_values']         
        _guess_val.update( guess_values )  
   
    _beta=_guess_val['beta']
    _alpha=_guess_val['alpha']
    _relaxation_rate = _guess_val['relaxation_rate']
    _baseline= _guess_val['baseline']
    
    pars  = mod.make_params( beta=_beta, alpha=_alpha, relaxation_rate =_relaxation_rate, baseline= _baseline)    
    for v in _vars:
        pars['%s'%v].vary = False
        
    if plot_g1:  
        ylabel='g1'
    else:
        ylabel='g2'
        
    if not one_plot:
        if num_rings!=1:
            #fig = plt.figure(figsize=(14, 10))
            fig = plt.figure(figsize=(12, 10))
            plt.axis('off')
            #plt.axes(frameon=False)
            #print ('here')
            plt.xticks([])
            plt.yticks([])

        else:
            fig = plt.figure(figsize=(8,8))

        #fig = plt.figure(figsize=(8,8))
        plt.title('uid= %s'%uid,fontsize=20, y =1.06)   

        for i in range(num_rings):
            ax = fig.add_subplot(sx, sy, i+1 )

            if fit_range is not None:
                y=g2[1:, i][fit_range[0]:fit_range[1]]
                lags=taus[1:][fit_range[0]:fit_range[1]]
            else:
                y=g2[1:, i]
                lags=taus[1:]


            result1 = mod.fit(y, pars, x =lags )


            #print ( result1.best_values)
            rate[i] = result1.best_values['relaxation_rate']
            #rate[i] = 1e-16
            beta[i] = result1.best_values['beta'] 

            #baseline[i] = 1.0
            baseline[i] =  result1.best_values['baseline'] 

            if function=='simple_exponential' or function=='simple':
                alpha[i] =1.0 
            elif function=='stretched_exponential' or function=='stretched':
                alpha[i] = result1.best_values['alpha']
                
            if plot_g1:
                ax.semilogx(taus[1:], ( g2[1:, i] - baseline[i] )/beta[i], 'bo')
                ax.semilogx(lags, (result1.best_fit- baseline[i] )/beta[i], '-r')            
            else:
                ax.semilogx(taus[1:], g2[1:, i], 'bo')
                ax.semilogx(lags, result1.best_fit, '-r')

            ax.set_title(" Q= " + '%.5f  '%(q_ring_center[i]) + r'$\AA^{-1}$')  
            #ax.set_ylim([min(y)*.95, max(y[1:]) *1.05])
            #ax.set_ylim([0.9999, max(y[1:]) *1.002])
            txts = r'$\tau$' + r'$ = %.3f$'%(1/rate[i]) +  r'$ s$'
            ax.text(x =0.02, y=.55, s=txts, fontsize=14, transform=ax.transAxes)     
            txts = r'$\alpha$' + r'$ = %.3f$'%(alpha[i])  
            #txts = r'$\beta$' + r'$ = %.3f$'%(beta[i]) +  r'$ s^{-1}$'
            ax.text(x =0.02, y=.45, s=txts, fontsize=14, transform=ax.transAxes)  

            txts = r'$baseline$' + r'$ = %.3f$'%( baseline[i]) 
            ax.text(x =0.02, y=.35, s=txts, fontsize=14, transform=ax.transAxes) 

            txts = r'$\beta$' + r'$ = %.3f$'%(beta[i]) #+  r'$ s^{-1}$'    
            ax.text(x =0.02, y=.25, s=txts, fontsize=14, transform=ax.transAxes) 

            if 'ylim' in kwargs:
                ax.set_ylim( kwargs['ylim'])
            elif 'vlim' in kwargs:
                vmin, vmax =kwargs['vlim']
                ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])
            else:
                ax.set_ylim([min(y)*.95, max(y[1:]) *1.05])
            if 'xlim' in kwargs:
                ax.set_xlim( kwargs['xlim'])

    else:
        fig = plt.figure(figsize=(8,8))
        #fig = plt.figure(figsize=(8,8))
        plt.title('uid= %s'%uid,fontsize=20, y =1.06)   
        ax = fig.add_subplot(111 )
        ax.set_ylabel(ylabel) 
        for i in range(num_rings):
            if fit_range is not None:
                y=g2[1:, i][fit_range[0]:fit_range[1]]
                lags=taus[1:][fit_range[0]:fit_range[1]]
            else:
                y=g2[1:, i]
                lags=taus[1:]
            result1 = mod.fit(y, pars, x =lags )
            #print ( result1.best_values)
            rate[i] = result1.best_values['relaxation_rate']
            #rate[i] = 1e-16
            beta[i] = result1.best_values['beta'] 
            #baseline[i] = 1.0
            baseline[i] =  result1.best_values['baseline'] 

            if function=='simple_exponential' or function=='simple':
                alpha[i] =1.0 
            elif function=='stretched_exponential' or function=='stretched':
                alpha[i] = result1.best_values['alpha']            
           
                
            if plot_g1:
                #print( baseline[i] , beta[i] )
                y= (g2[1:, i] - baseline[i] )/beta[i]
                ax.semilogx(taus[1:], y,
                            next(markers),color=next(colors),
                            label = "Q= " + '%.5f  '%(q_ring_center[i]) + r'$\AA^{-1}$' )
                
                ax.semilogx(lags, (result1.best_fit- baseline[i] )/beta[i], '-',
                            color=next(colors_copy) )            
            else:
                ax.semilogx(taus[1:], g2[1:, i], 
                    next(markers),label = "Q= " + '%.5f  '%(q_ring_center[i]) + r'$\AA^{-1}$' )
                ax.semilogx(lags, result1.best_fit, '-r')             

        if 'ylim' in kwargs:
            ax.set_ylim( kwargs['ylim'])
        elif 'vlim' in kwargs:
            vmin, vmax =kwargs['vlim']
            ax.set_ylim([min(y)*vmin, max(y[1:])*vmax ])
        else:
            ax.set_ylim([min(y)*.95, max(y[1:]) *1.05])
        if 'xlim' in kwargs:
            ax.set_xlim( kwargs['xlim'])
                
        plt.legend(loc='best', fontsize=10)
                
    #dt =datetime.now()
    #CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)        
         
    #fp = path + 'g2--uid=%s'%(uid) + CurTime + '--Fit.png'
    fp = path + 'uid=%s--%s'%(uid,ylabel) + '--fit-.png'
    fig.savefig( fp, dpi=fig.dpi)        
    
    fig.tight_layout()       
    plt.show()

    result = dict( beta=beta, rate=rate, alpha=alpha, baseline=baseline )
    
    return result



def power_func(x, D0, power=2):
    return D0 * x**power



def fit_q_rate( q, rate, plot_=True, power_variable=False, *argv,**kwargs): 
    '''
    Option:
        if power_variable = False, power =2 to fit q^2~rate, 
                Otherwise, power is variable.
    '''
    x=q
    y=rate
        
    if 'fit_range' in kwargs.keys():
        fit_range = kwargs['fit_range']         
    else:    
        fit_range= None

    if 'uid' in kwargs.keys():
        uid = kwargs['uid'] 
    else:
        uid = 'uid' 

    if 'path' in kwargs.keys():
        path = kwargs['path'] 
    else:
        path = ''    

    if fit_range is not None:
        y=rate[fit_range[0]:fit_range[1]]
        x=q[fit_range[0]:fit_range[1]] 
        
    mod = Model( power_func )
    #mod.set_param_hint( 'power',   min=0.5, max= 10 )
    #mod.set_param_hint( 'D0',   min=0 )
    pars  = mod.make_params( power = 2, D0=1*10^(-5) )
    if power_variable:
        pars['power'].vary = True
    else:
        pars['power'].vary = False
        
    _result = mod.fit(y, pars, x = x )
    
    D0  = _result.best_values['D0']
    power= _result.best_values['power']
    
    print ('The fitted diffusion coefficient D0 is:  %.3e   A^2S-1'%D0)
    if plot_:
        fig,ax = plt.subplots(  figsize=(8,8) )        
        plt.title('Q%s-Rate--uid= %s_Fit'%(power,uid),fontsize=20, y =1.06)  
        
        ax.plot(q**power,rate, 'bo')
        ax.plot(x**power, _result.best_fit,  '-r')
        
        txts = r'$D_0: %.3e$'%D0 + r' $A^2$' + r'$s^{-1}$'
        
        ax.text(x =0.05, y=.75, s=txts, fontsize=28, transform=ax.transAxes)       
        
        
        ax.set_ylabel('Relaxation rate 'r'$\gamma$'"($s^{-1}$)")
        ax.set_xlabel("$q^%s$"r'($\AA^{-2}$)'%power)
              
        dt =datetime.now()
        CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)     
        #fp = path + 'Q%s-Rate--uid=%s'%(power,uid) + CurTime + '--Fit.png'
        fp = path + 'uid=%s--Q-Rate'%(uid) + '--fit-.png'
        fig.savefig( fp, dpi=fig.dpi)    
    
        fig.tight_layout() 
        plt.show()
        
    return D0


def get_fit_q_rate( q, rate,  power_variable=False, *argv,**kwargs): 
    '''
    Option:
        if power_variable = False, power =2 to fit q^2~rate, 
                Otherwise, power is variable.
    '''
    x=q
    y=rate
        
    if 'fit_range' in kwargs.keys():
        fit_range = kwargs['fit_range']         
    else:    
        fit_range= None  

    if fit_range is not None:
        y=rate[fit_range[0]:fit_range[1]]
        x=q[fit_range[0]:fit_range[1]] 
        
    mod = Model( power_func )
    #mod.set_param_hint( 'power',   min=0.5, max= 10 )
    #mod.set_param_hint( 'D0',   min=0 )
    pars  = mod.make_params( power = 2, D0=1*10^(-5) )
    if power_variable:
        pars['power'].vary = True
    else:
        pars['power'].vary = False
        
    _result = mod.fit(y, pars, x = x )
    
    D0  = _result.best_values['D0']
    power= _result.best_values['power']
    
    print ('The fitted diffusion coefficient D0 is:  %.3e   A^2S-1'%D0) 
        
    return _result


def plot_fit_q_rate( q, rate, fit_results, return_fig = False, *argv,**kwargs):
    if 'uid' in kwargs.keys():
        uid = kwargs['uid'] 
    else:
        uid = 'uid' 

    if 'path' in kwargs.keys():
        path = kwargs['path'] 
    else:
        path = ''

    x=q
    y=rate
        
    if 'fit_range' in kwargs.keys():
        fit_range = kwargs['fit_range']         
    else:    
        fit_range= None  

    if fit_range is not None:
        y=rate[fit_range[0]:fit_range[1]]
        x=q[fit_range[0]:fit_range[1]]
        
    D0  = fit_results.best_values['D0']
    power= fit_results.best_values['power']
    
    fig = Figure()
    ax = fig.add_subplot(111)        
    plt.title('Q%s-Rate--uid= %s_Fit'%(power,uid),fontsize=20, y =1.06)      
    ax.plot(q**power,rate, 'bo')
    ax.plot(x**power,fit_results.best_fit,  '-r')   

    
    txts = r'$D0: %.3e$'%D0 + r' $A^2$' + r'$s^{-1}$'    
    ax.text(x =0.15, y=.75, s=txts, fontsize=14, transform=ax.transAxes)     
    ax.set_ylabel('Relaxation rate 'r'$\gamma$'"($s^{-1}$)")
    ax.set_xlabel("$q^%s$"r'($\AA^{-2}$)'%power)
          
    fp = path + 'uid=%s--Q-Rate'%(uid) + '--fit-.png'
    plt.savefig( fp, dpi=fig.dpi)
    fig.set_tight_layout(True)   
    #plt.show()

    if return_fig:
        return fig 


    

def linear_fit( x,y):
    D0 = np.polyfit(x, y, 1)
    gmfit = np.poly1d(D0)    
    return D0, gmfit


def fit_q2_rate( q2, rate, plot_=True, *argv,**kwargs): 
    x= q2
    y=rate
        
    if 'fit_range' in kwargs.keys():
        fit_range = kwargs['fit_range']         
    else:    
        fit_range= None

    if 'uid' in kwargs.keys():
        uid = kwargs['uid'] 
    else:
        uid = 'uid' 

    if 'path' in kwargs.keys():
        path = kwargs['path'] 
    else:
        path = ''    

    if fit_range is not None:
        y=rate[fit_range[0]:fit_range[1]]
        x=q2[fit_range[0]:fit_range[1]] 
    
    D0, gmfit = linear_fit( x,y)
    print ('The fitted diffusion coefficient D0 is:  %.2E   A^2S-1'%D0[0])
    if plot_:
        fig,ax = plt.subplots()
        plt.title('Q2-Rate--uid= %s_Fit'%uid,fontsize=20, y =1.06) 
        ax.plot(q2,rate, 'ro', ls='')
        ax.plot(x,  gmfit(x),  ls='-')        
        txts = r'$D0: %.2f$'%D0[0] + r' $A^2$' + r'$s^{-1}$'
        ax.text(x =0.15, y=.75, s=txts, fontsize=14, transform=ax.transAxes)         
        
        ax.set_ylabel('Relaxation rate 'r'$\gamma$'"($s^{-1}$)")
        ax.set_xlabel("$q^2$"r'($\AA^{-2}$)')              
        dt =datetime.now()
        CurTime = '%s%02d%02d-%02d%02d-' % (dt.year, dt.month, dt.day,dt.hour,dt.minute)     
        #fp = path + 'Q2-Rate--uid=%s'%(uid) + CurTime + '--Fit.png'
        fp = path + 'uid=%s--Q2-Rate'%(uid) + '--fit-.png'
        fig.savefig( fp, dpi=fig.dpi)    
    
        fig.tight_layout() 
        plt.show()
        
    return D0



def plot_gamma():
    '''not work'''
    fig, ax = plt.subplots()
    ax.set_title('Uid= %s--Beta'%uid)
    ax.set_title('Uid= %s--Gamma'%uid)
    #ax.plot(  q_ring_center**2 , 1/rate, 'ro', ls='--')

    ax.loglog(  q_ring_center , 1/result['rate'], 'ro', ls='--')
    #ax.set_ylabel('Log( Beta0 'r'$\beta$'"($s^{-1}$)")
    ax.set_ylabel('Log( Gamma )')
    ax.set_xlabel("$Log(q)$"r'($\AA^{-1}$)')
    plt.show()

    



def multi_uids_saxs_xpcs_analysis(   uids, md, run_num=1, sub_num=None, good_start=10, good_end= None,
                                  force_compress=False,
                                  fit = True, compress=True, para_run=False  ):
    ''''Aug 16, 2016, YG@CHX-NSLS2
    Do SAXS-XPCS analysis for multi uid data
    uids: a list of uids to be analyzed    
    md: metadata, should at least include
        mask: array, mask data
        data_dir: the path to save data, the result will be saved in data_dir/uid/...
        dpix:
        Ldet:
        lambda:
        timeperframe:
        center
    run_num: the run number
    sub_num: the number in each sub-run
    fit: if fit, do fit for g2 and show/save all fit plots
    compress: apply a compress algorithm
    
    Save g2/metadata/g2-fit plot/g2 q-rate plot/ of each uid in data_dir/uid/...
    return:
    g2s: a dictionary, {run_num: sub_num: g2_of_each_uid}   
    taus,
    use_uids: return the valid uids
    '''
    
    
    g2s = {} # g2s[run_number][sub_seq]  =  g2 of each uid
    lag_steps = [0]    
    useful_uids = {}
    if sub_num is None:
        sub_num = len( uids )//run_num    

    mask = md['mask']    
    data_dir = md['data_dir']
    ring_mask = md['ring_mask']
    q_ring_center = md['q_ring_center']
    
    for run_seq in range(run_num):
        g2s[ run_seq + 1] = {}    
        useful_uids[ run_seq + 1] = {}  
        i=0    
        for sub_seq in range(  0, sub_num   ):   
            #good_end=good_end
            
            uid = uids[ sub_seq + run_seq * sub_num  ]        
            print( 'The %i--th uid to be analyzed is : %s'%(i, uid) )
            try:
                detector = get_detector( db[uid ] )
                imgs = load_data( uid, detector, reverse= True   )  
            except:
                print( 'The %i--th uid: %s can not load data'%(i, uid) )
                imgs=0

            data_dir_ = os.path.join( data_dir, '%s/'%uid)
            os.makedirs(data_dir_, exist_ok=True)

            i +=1            
            if imgs !=0:            
                imgsa = apply_mask( imgs, mask )
                Nimg = len(imgs)
                md_ = imgs.md  
                useful_uids[ run_seq + 1][i] = uid
                if compress:
                    filename = '/XF11ID/analysis/Compressed_Data' +'/uid_%s.cmp'%uid                     
                    mask, avg_img, imgsum, bad_frame_list = compress_eigerdata(imgs, mask, md_, filename, 
                                    force_compress= force_compress, bad_pixel_threshold= 5e9,nobytes=4,
                                            para_compress=True, num_sub= 100)                     
                    try:
                        md['Measurement']= db[uid]['start']['Measurement']
                        #md['sample']=db[uid]['start']['sample']     
                        #md['sample']= 'PS205000-PMMA-207000-SMMA3'
                        print( md['Measurement'] )

                    except:
                        md['Measurement']= 'Measurement'
                        md['sample']='sample'                    

                    dpix = md['x_pixel_size'] * 1000.  #in mm, eiger 4m is 0.075 mm
                    lambda_ =md['incident_wavelength']    # wavelegth of the X-rays in Angstroms
                    Ldet = md['detector_distance'] * 1000      # detector to sample distance (mm)
                    exposuretime= md['count_time']
                    acquisition_period = md['frame_time']
                    timeperframe = acquisition_period#for g2
                    #timeperframe = exposuretime#for visiblitly
                    #timeperframe = 2  ## manual overwrite!!!! we apparently writing the wrong metadata....
                    center= md['center']

                    setup_pargs=dict(uid=uid, dpix= dpix, Ldet=Ldet, lambda_= lambda_, 
                                timeperframe=timeperframe, center=center, path= data_dir_)

                    md['avg_img'] = avg_img                  
                    #plot1D( y = imgsum[ np.array( [i for i in np.arange( len(imgsum)) if i not in bad_frame_list])],
                    #   title ='Uid= %s--imgsum'%uid, xlabel='Frame', ylabel='Total_Intensity', legend=''   )
                    min_inten = 10

                    #good_start = np.where( np.array(imgsum) > min_inten )[0][0]
                    good_start = good_start
                    
                    if good_end is None:
                        good_end_ = len(imgs)
                    else:
                        good_end_= good_end
                    FD = Multifile(filename, good_start, good_end_ )                         
                        
                    good_start = max(good_start, np.where( np.array(imgsum) > min_inten )[0][0] ) 
                    print ('With compression, the good_start frame number is: %s '%good_start)
                    print ('The good_end frame number is: %s '%good_end_)
                    
                    hmask = create_hot_pixel_mask( avg_img, 1e8)
                    qp, iq, q = get_circular_average( avg_img, mask * hmask, pargs=setup_pargs, nx=None,
                            plot_ = False, show_pixel= True, xlim=[0.001,.05], ylim = [0.0001, 500])                

                    norm = get_pixelist_interp_iq( qp, iq, ring_mask, center)
                    if not para_run:
                        g2, lag_steps_  =cal_g2c( FD,  ring_mask, bad_frame_list,good_start, num_buf = 8, 
                                imgsum= None, norm= norm )  
                    else:
                        g2, lag_steps_  =cal_g2p( FD,  ring_mask, bad_frame_list,good_start, num_buf = 8, 
                                imgsum= None, norm= norm )  

                    if len( lag_steps) < len(lag_steps_):
                        lag_steps = lag_steps_
                    
                    FD=0
                    avg_img, imgsum, bad_frame_list = [0,0,0]
                    md['avg_img']=0
                    imgs=0

                else:
                    sampling = 1000  #sampling should be one  

                    #good_start = check_shutter_open( imgsra,  min_inten=5, time_edge = [0,10], plot_ = False )
                    good_start = good_start

                    good_series = apply_mask( imgsa[good_start:  ], mask )

                    imgsum, bad_frame_list = get_each_frame_intensity(good_series ,sampling = sampling, 
                                        bad_pixel_threshold=1.2e8,  plot_ = False, uid=uid)
                    bad_image_process = False

                    if  len(bad_frame_list):
                        bad_image_process = True
                    print( bad_image_process  ) 

                    g2, lag_steps_  =cal_g2( good_series,  ring_mask, bad_image_process,
                                       bad_frame_list, good_start, num_buf = 8 )
                    if len( lag_steps) < len(lag_steps_):
                        lag_steps = lag_step_
                
                taus_ = lag_steps_ * timeperframe
                taus = lag_steps * timeperframe
                
                res_pargs = dict(taus=taus_, q_ring_center=q_ring_center, path=data_dir_, uid=uid        )
                save_saxs_g2(   g2, res_pargs )
                #plot_saxs_g2( g2, taus,  vlim=[0.95, 1.05], res_pargs=res_pargs) 
                if fit:
                    fit_result = fit_saxs_g2( g2, res_pargs, function = 'stretched',  vlim=[0.95, 1.05], 
                        fit_variables={'baseline':True, 'beta':True, 'alpha':False,'relaxation_rate':True},
                        guess_values={'baseline':1.0,'beta':0.05,'alpha':1.0,'relaxation_rate':0.01})
                    fit_q_rate(  q_ring_center[:], fit_result['rate'][:], power_variable= False,
                           uid=uid, path= data_dir_ )

                    psave_obj( fit_result, data_dir_ + 'uid=%s-g2-fit-para'%uid )
                psave_obj(  md, data_dir_ + 'uid=%s-md'%uid ) #save the setup parameters

                g2s[run_seq + 1][i] = g2            
                print ('*'*40)
                print()

        
    return g2s, taus, useful_uids
    
    
    
def plot_mul_g2( g2s, md ):
    '''
    Plot multi g2 functions generated by  multi_uids_saxs_xpcs_analysis
    Will create a large plot with q_number pannels
    Each pannel (for each q) will show a number (run number of g2 functions     
    '''
    
    q_ring_center = md['q_ring_center']    
    sids = md['sids'] 
    useful_uids = md['useful_uids'] 
    taus =md['taus'] 
    run_num = md['run_num'] 
    sub_num =  md['sub_num'] 
    uid_ = md['uid_']

    fig = plt.figure(figsize=(12, 20)) 
    plt.title('uid= %s:--->'%uid_ ,fontsize=20, y =1.06) 

    Nq = len(q_ring_center)
    if Nq!=1:            
        plt.axis('off')                 
    sx = int(round(np.sqrt(  Nq  )) )

    if Nq%sx == 0: 
        sy = int(Nq/sx)
    else: 
        sy=int(Nq/sx+1) 

    for sn in range( Nq ):
        ax = fig.add_subplot(sx,sy,sn+1 )
        ax.set_ylabel( r"$g_2$" + '(' + r'$\tau$' + ')' ) 
        ax.set_xlabel(r"$\tau $ $(s)$", fontsize=16) 

        for run_seq in range(run_num): 
            i=0    
            for sub_seq in range(  0, sub_num   ): 
                #print( run_seq, sub_seq )
                uid = useful_uids[run_seq +1][ sub_seq +1 ] 
                sid = sids[i]
                if i ==0:
                    title = r'$Q_r= $'+'%.5f  '%( q_ring_center[sn]) + r'$\AA^{-1}$' 
                    ax.set_title( title , y =1.1, fontsize=12) 
                y=g2s[run_seq+1][sub_seq+1][:, sn]
                len_tau = len( taus ) 
                len_g2 = len( y )
                len_ = min( len_tau, len_g2)

                #print ( len_tau, len(y))
                #ax.semilogx(taus[1:len_], y[1:len_], marker = '%s'%next(markers_), color='%s'%next(colors_), 
                #            markersize=6, label = '%s'%sid) 
                
                ax.semilogx(taus[1:len_], y[1:len_], marker =  markers[i], color= colors[i], 
                            markersize=6, label = '%s'%sid)                 
                
                if sn ==0:
                    ax.legend(loc='best', fontsize = 6)

                i = i + 1
    fig.set_tight_layout(True)    
 
                
                
            
            
    