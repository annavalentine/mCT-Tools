#!/usr/bin/env python
# coding: utf-8

# In[4]:


## Import libraries
import codecs
import shutil
import numpy as np
import pandas as pd 
import os
import io


# In[5]:


#general takes a path and spits out all of the file names 
def list_files_local(path):
    """ Get file list form local folder. """
    from glob import glob
    return glob(path)


# In[6]:



#Converts files from ANSCI to UTF8 (which python can read), dumps them in a UTF8 folder inside folder path
def UTF8_convert(path):
    BLOCKSIZE = 300000 # desired size in bytes, this is 300 kB, which is larger than biggest file 
    
    # files to be converted
    list_files = list_files_local(path+"/*.txt")
    
    ## create folder inside path for UTF8 files
    folder = path + '/UTF8/'
    if not os.path.exists(folder):
            os.makedirs(folder)
            
    for file in list_files: 
        #naming convention and moves to folder for UTF8-Files
        og_fname = os.path.split(file)  # get original file name
        fname = folder + og_fname[1][:-4] + '_UTF8.txt'  #put in new folder and take off .txt, replace with UTF8.txt
        try: 
            with io.open(file, "r") as sourceFile:
                with io.open(fname, "w", encoding="utf-8") as targetFile:     # convert to UTF-8
                    while True:
                        contents = sourceFile.read(BLOCKSIZE)
                        if not contents:
                            break
                        targetFile.write(contents)
        except:
            print("Convert failed on file: ", fname)
    


# In[7]:


# gives the sample depth (lower) from the file name
def sample_height(file):
    #Find scan depth,
    sc = file.split("_") #This read from file name
    scan_depth_tot = sc[4]
    sc2 = scan_depth_tot.split("-")
    num = float(sc2[0])
    
    return num


# In[8]:


#Find the term in the file (used for knowing where to start dataframe)
def find_term(term, file):
    row = 0
    file_o = open(file)
    for line in file_o:
        row += 1
        line.strip().split('/n')
        if term in line:
            return (row)
    file.close()


# In[9]:


#Loop through all of the files in the snowpit and concatonates in one dataframe
def loop_files(path, verbose):
    
    files = list_files_local(path)

    
    #start and end terms
    start = "2D analysis"
    end = "3D analysis"
    frames = []

    for file in files:
        #Find start row, read in csv for Morpho Result
        end_row = (find_term(end, file)-4)
        start_row = find_term(start, file)+9
        nrow = end_row - start_row
        df_int = pd.read_csv(file, skiprows= (start_row), nrows=(nrow))
        
        ### MAKE SOME ADJUSTMENTS
        df_int = df_int.drop([df_int.index[0]])   #Drop units row
        df_int = df_int.drop(columns=['Unnamed: 39']) # drop this random column?
        df_int = df_int.rename(columns={'Unnamed: 0':'File Name'})  #rename column
        
        ### SCAN DEPTH:
        #Grab that smaller height num
        #print(df_int['File Name'].tolist()[0])
        fname = df_int['File Name'].tolist()[0]
        sc = fname.split("_") #This read from file name
        scan_depth = sc[1]
        if (len(scan_depth)<4):
            scan_depth = sc[1]+'-'+sc[2]
            if verbose:
                print("scan depth typo on file:", fname, "CORRECTION: ", scan_depth)
           

        #find average depth
        cutoff = scan_depth[0:-2]
        x = cutoff.split("-")
        
        ### Add in some rows for this prelim info
        ### Description, Abbreviation, Value, Unit
        df_int['Scan Depth'] = [scan_depth]*len(df_int) # Row for Scan Depth

        

        #Add the column we want ("Values") to the datafram
        frames.append(df_int)
       

    result = pd.concat(frames)
        
    return result 
    
    


# In[11]:


def add_z_depth(df):
    
    #Z.Pos
    df["Pos.Z"] = (df["Pos.Z"].astype(float))*0.1
    Z_Pos = df["Pos.Z"].tolist()
    
    ## Scan depth
    scan_depth = df["Scan Depth"].tolist()
    
    
    Z_col = []
    
    for i in range(len(Z_Pos)):
        z = Z_Pos[i]
        
        ## Scan depth
        sc = scan_depth[i].split("-")
        low = sc[1]
        low = float(low[:-2])
        
        z_depth = z + low
        
        
        Z_col.append(z_depth)
    
  
    df['Depth.Z'] = Z_col
    
    ### Sort by depth values
    df = df.sort_values(by=['Depth.Z'])
    
    return df


# In[12]:


def convert(path, **kwargs):
    
    ## get output folder path (only for multiple file conversion)
    outpath = kwargs.get('outpath', None)
    
    ## get pitname if individual pit needed
    pitname = kwargs.get('pitname',None)
    
    ## output to .csv 
    to_csv = kwargs.get('to_csv', True)
    
    ## verbose 
    verbose = kwargs.get('verbose', True)
    
    #######################################################
    
    ## ONE SNOWPIT (FOLDER)
    if pitname != None: 
        #pit_files = list_files_local(path+'*'+pitname+'/*')
        
        #Convert to UTF-8
        UTF8_convert(path + pitname)
        
        #Loop through the slice files
        result = loop_files(path + pitname + '/UTF8/*', verbose)
        result = add_z_depth(result)
        
        #If to .csv is wanted: 
        if to_csv:
            # Export our dataframe to a .csv 
            if outpath: 
                if not os.path.exists(outpath):
                        os.makedirs(outpath)
                        
                result.to_csv(outpath+"MCT_2D"+pitname+".csv", index =False)
                if verbose: 
                    print(".csv saved to:", outpath+"MCT_2D"+pitname+".csv" )
            else:
                result.to_csv("MCT_2D"+pitname+".csv", index =False)
                if verbose: 
                    print(".csv saved to:", os.getcwd()+"/MCT_2D"+pitname+".csv" )
                
        return result 
        
    ##### ALL SNOWPITS (Many folders of mCT data)
    list_files = list_files_local(path + '*')
    pitnames = []
    if verbose: 
        print("Folders to Convert:")
        for file in list_files: print(os.path.split(file)[1])
        print("######################### \n")
    
    ### Loop over each folder, place in new folder
    for file in list_files:
        try: 
            pitname = os.path.split(file)[1]

            #Convert to UTF-8
            UTF8_convert(path + pitname)

            ## loop through slice files
            result = loop_files(path + pitname + '/UTF8/*', verbose)
            result = add_z_depth(result)

            ### default to .csv 
            if to_csv:
                ## if a path to a folder for results given
                if outpath: 
                    if not os.path.exists(outpath):
                        os.makedirs(outpath)
                        
                    result.to_csv(outpath+"MCT_2D"+pitname+".csv", index =False)
                    if verbose: 
                        print(pitname, " .csv saved to:", outpath+"MCT_2D"+pitname+".csv" )

                # if no output path given, make a folder inside data folder: 
                else: 
                    result.to_csv("MCT_2D"+pitname+".csv", index =False)
                    if verbose: 
                        print(".csv saved to:", os.getcwd()+"/MCT_2D"+pitname+".csv" )

        except: 
            print("Fail on File:", file)
            pass
                     
    print("######################### \nPROCESS FINISHED")

