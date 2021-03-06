import matplotlib as mpl
import numpy as np
import matplotlib.pyplot as plt

class GeneratedLatticeImage():
    ''' A generated data object
    Attributes:
        N : integer
            number of lattice sites along one direction (NxN)
        M : integer
            number of camera pixels per lattice site along one direction (MxM)
        x_loc : ndarray of ints
            x positions of all photon counts due to CCD dark counts and atom fluorescence
        y_loc : ndarray of ints
            y positions of all photon counts due to CCD dark counts and atom fluorescence
        actual_lattice : 2d ndarray of ints
            2d grid representing true filling of optical lattice
        pixel_grid : 2d ndarray of ints
            2d grid of CCD intensity values

    '''

    def __init__(self, N, M, N_atom, N_photon, CCD_resolution = 1024, lattice_origin = (400,600), std=10, N_backg=2000, lam_backg=200):
        '''
        Generates positions of photon counts and CCD intensity values from the randomly placed atoms on a lattice and from Poissonian 
        dark counts. Includes full CCD data with dedicated optical lattice region.
        
        Parameters
        ----------
        N : integer
            number of lattice sites along one direction (NxN)
        M : integer
            number of camera pixels per lattice site along one direction (MxM)
        N_atom : integer
            total number of atoms on the lattice
        N_photon : integer
            number of photons sampled from an atom
        CCD_resolution : integer
            number of pixels along one axis of CCD
        lattice_origi n: tuple of integers
            top left corner of optical lattice region. Optical lattice region is (M*N)x(M*N) pixels large.
        std : float
            standard deviation of the Gaussian that is sampled from
        N_backg : integer
            number of samples drawn from the Poisson distribution for the background noise
        lam_back : float
            expectation interval of the Poisson dark count event

        Returns
        -------
        xloc, yloc : ndarrays
            x and y positions of all the photon counts
        actual_lattice : 2d ndarray of ints
            N*M x N*M grid representing true filling of optical lattice
        pixel_grid : 2d ndarray of ints
            CCD_resolution x CCD resolution grid of CCD intensity values
        '''

        # Store Dimensions and std
        self.N = N
        self.M = M
        self.std = std
        self.lattice_origin = lattice_origin

        #Randomly place atoms on the lattice
        atom_location = np.random.choice(np.arange(N*N), N_atom, replace=False) #pick atom position randomly from NxN array

        actual_lattice = np.zeros((N,N))
        atom_location_index = np.unravel_index(atom_location,(N,N))

        #Store actual occupation of the atoms for future comparison with the inferred one
        for x,y in zip(atom_location_index[0],atom_location_index[1]):
            actual_lattice[y,x] = 1
            # Uncomment for inverted y
            # actual_lattice[N-y-1,x] = 1

        atom_location_index = atom_location_index + np.zeros((2, N_atom))*M*N #convert the atom location number to x,y atom location index

        atom_location_index = atom_location_index*M + M/2
        x_index = atom_location_index[0,:] #atoms x location
        y_index = N*M - atom_location_index[1,:] #atoms y location

        pixel_grid = np.zeros((CCD_resolution,CCD_resolution))

        #For each atom sample photons from a Gaussian centered on the lattice site, combine the x,y positions of the counts
        x_loc = np.array([])
        y_loc = np.array([])
        for i in range(N_atom):
            xx, yy = np.random.multivariate_normal([x_index[i], y_index[i]], [[std, 0], [0, std]], N_photon).T #at each atom location sample N_photons from a Gaussian
            # Round and cast photon positions to respect pixel postions 
            xx = np.rint(xx).astype(int) + lattice_origin[0]
            yy = np.rint(yy).astype(int) + lattice_origin[1]
            x_loc = np.concatenate((x_loc, xx)) #combine the sampled x-locations for each atom
            y_loc = np.concatenate((y_loc, yy)) #combine the sampled y-locations for each atom

        #Generate dark counts which is the background noise of the camera. Combine dark photon locations with scattered photon locations.
        CCD_x = np.arange(0, CCD_resolution, 1) #x-pixel locations
        CCD_y = np.arange(0, CCD_resolution, 1) #y-pixel locations
        #dark_count = np.random.poisson(lam_backg, N_backg) #create dark counts sampling from a Poisson distribution, this gives numbers corresponding to number of dark counts
	dark_count_tot=np.random.poisson(lam_backg*N_backg) #Also the arguments can be combined simply to total dark counts
        dark_count_location_x = np.random.choice(CCD_x,dark_count_tot, replace=True) #pick a random x location for the dark counts
        dark_count_location_y = np.random.choice(CCD_y,dark_count_tot, replace=True) #pick a random y location for the dark counts

        x_loc = np.concatenate((x_loc, dark_count_location_x)).astype(int) #combine the sampled x-locations from atoms and dark counts
        y_loc = np.concatenate((y_loc, dark_count_location_y)).astype(int) #combine the sampled y-locations from atoms and dark counts

        #convert counts to intensity values for each pixel

        for x,y in zip(x_loc,y_loc):
            if(x<CCD_resolution and y<CCD_resolution and x>0 and y>0):
                # pixel_grid[CCD_resolution-y-1,x] += 1
                pixel_grid[y,x] += 1

        #Shift and scale counts to mimic data from CCD
        pixel_grid *= 5000/pixel_grid.max()
        pixel_grid += 600
        
        # Store output results
        self.x_loc = x_loc
        self.y_loc = y_loc
        self.actual_lattice = actual_lattice
        self.pixel_grid = pixel_grid

        

    # useful for checking that each count sits in the middle of a pixel
    # isolates a particular part of the generated photon counts to more
    # easily see each pixel
    def grid_plot(self, num_sites=1, invert_y = False):
        '''Plot the image (collected photons) on the camera.'''
        fig = plt.figure(figsize=(8, 8), dpi=100)
        ax = fig.add_subplot(1,1,1)
        xlims = (self.lattice_origin[0],self.lattice_origin[0]+self.N*self.M)
        ylims = (self.lattice_origin[1],self.lattice_origin[1]+self.N*self.M)
        coords = np.zeros((2,len(self.x_loc)),dtype=int)
        coords[0,:] = self.x_loc
        coords[1,:] = self.y_loc
        coords = coords.T
        lattice_coords = coords[(coords[:,0]>xlims[0])*(coords[:,0]<xlims[1])*(coords[:,1]>ylims[0])*(coords[:,1]<ylims[1]),:]
        reduced_lattice_coords = lattice_coords[(lattice_coords[:,0] < (num_sites*self.M + xlims[0]))*(lattice_coords[:,1] < (num_sites*self.M + ylims[0]))]
        im = plt.plot(reduced_lattice_coords.T[0], reduced_lattice_coords.T[1], 'ko', markersize=1,alpha=0.25) #plot counts
        
        ax.set_xticks(np.arange(-0.5-1*self.M, (num_sites+1)*self.M+0.5, 1) + xlims[0]) #vertical lines as visual aid
        ax.set_yticks(np.arange(-0.5-1*self.M, (num_sites+1)*self.M+0.5, 1) + ylims[0]) #horizontal lines as visual aid
        ax.grid(True, color="black")

        if(invert_y):
            ax.invert_yaxis()

    def plot(self,invert_y = False):
        '''Plot the image (collected photons) on the camera.'''
        fig = plt.figure(figsize=(8, 8), dpi=100)
        ax = fig.add_subplot(1,1,1)
        im = plt.plot(self.x_loc, self.y_loc, 'k.', markersize=0.1) #plot counts
        ax.set_xticks(np.arange(-0.5-1*self.M, (self.N+1)*self.M+0.5, self.M) + self.lattice_origin[0]) #vertical lines as visual aid
        ax.set_yticks(np.arange(-0.5-1*self.M, (self.N+1)*self.M+0.5, self.M) + self.lattice_origin[1]) #horizontal lines as visual aid
        ax.grid(True, color="red")
        if(invert_y):
            ax.invert_yaxis()

        #I'm (EK) not sure what the below is but it seems to have been added by Furkan, so I'm leaving it in.
        self.center_points = np.zeros((self.N, self.N, 2))

        # Store center points
        for nx in range(self.N):
            for ny in range(self.N):
                self.center_points[nx, ny] = [self.M / 2 + nx * self.M, self.M / 2 + ny * self.M]
