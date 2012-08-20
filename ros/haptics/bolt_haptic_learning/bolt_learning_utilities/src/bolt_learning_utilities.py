#!/usr/bin/env python
import roslib; roslib.load_manifest("bolt_learning_utilities")
import rospy
import numpy as np
import cPickle
import convert_h5_dataset_to_bolt_obj as converth5
import process_adjective_labels
from random import shuffle

from bolt_feature_obj import BoltFeatureObj
# Convert h5 files to BolPR2MotionObj data
def convertH5ToBoltObjFile(input_file, output_file, save_to_file):
    """
    Convert data in h5 file into a single pkl file that 
    stores the information in a BoltPR2MotionObj.  
    The runs are segmented by motion and stored in a dictionary.

    Usage: convertH5ToBoltObjFile(input_file, output_file, save_to_file)
   
    Note: The function returns a dictionary that can also be saved directly
          to a pickle file.  However, if save_to_file is False, it will not
          be saved and it is up to the user to store the returned object
 
    input_file - .h5
    output_file - .pkl
    save_to_file - boolean

    Output structure:
        
        Dictionary -> "squeeze", "thermal_hold", "tap", "slide",
                      "slow_slide"

        "squeeze" -> list(BoltPR2MotionObjs)

    """

    # Call the function
    loaded_data = converth5.load_data(input_file, output_file, save_to_file)

    return loaded_data


# Load bolt obj pickle file
def loadBoltObjFile(input_file):
    """
    Takes a path to a pkl file, loads, and returns the dictionary.  See
    convertH5ToBoltObjFile for the data structure returned
    """
    # File checking
    if not input_file.endswith(".pkl"):
        raise Exception("Input file: %s is not a pkl file.\n Please pass in pkl file with extention .pkl" % input_file)
    
    # Load the file 
    file_ptr = open(input_file, "r")
    loaded_data = cPickle.load(file_ptr)

    return loaded_data



# Insert adjective labels 
def insertAdjectiveLabels(input_boltPR2Motion, output_file, adjective_file, save_to_file):
    """
    Adjective label file is given as a pytable in h5 data

    Given either a path to a pkl file or the direct dictionary of 
    boltPR2MotionObj, will insert the labels
    
    if input_boltPR2Motion is a file, the function will first load the
    file before inserting adjectives

    """
    
    if isinstance(input_boltPR2Motion, str):
        data = process_adjective_labels.load_files(input_boltPR2Motion)
    else:
        data = input_boltPR2Motion

    data_with_adjectives = process_adjective_labels.populate_BoltPR2MotionObj(data, output_file, adjective_file, save_to_file)

    return data_with_adjectives



# Normalizes the given bolt_obj.  Works directly on the object
def normalize_data(bolt_obj, discard_raw_flag = True):
    """ 
    Given a BOLTPR2MotionObj 
    Normalize the data
        - Takes the mean and subtract 
        - Adds a pac_flat field

    Usage: normalize(bolt_obj, discard_flag)
        
        Discard flag is optional - default is True
        Discard flag set False will keep the original raw
        data, which makes the data twice as large
    """
    
    num_fingers = len(bolt_obj.electrodes)

    # For each finger normalize and store
    for finger in xrange(num_fingers):
        # Electrodes
        electrodes = bolt_obj.electrodes[finger]
        electrodes_mean = bolt_obj.electrodes_mean[finger]
        bolt_obj.electrodes_normalized.append(-(electrodes - np.mean(electrodes_mean, axis = 0)))

        # PDC
        pdc = bolt_obj.pdc[finger]
        pdc_mean = bolt_obj.pdc_mean[finger]
        bolt_obj.pdc_normalized.append(pdc - np.mean(pdc_mean))

        # TDC
        tdc = bolt_obj.tdc[finger]
        tdc_mean = bolt_obj.tdc_mean[finger]
        bolt_obj.tdc_normalized.append(tdc - np.mean(tdc_mean))

        # TAC
        tac = bolt_obj.tac[finger]
        tac_mean = bolt_obj.tac_mean[finger]
        bolt_obj.tac_normalized.append(-(tac - np.mean(tac_mean)))

        # PAC
        pac = bolt_obj.pac[finger]
        pac_mean = bolt_obj.pac_mean[finger]
        pac_norm = -(pac - np.mean(pac_mean, axis = 0)) 
        bolt_obj.pac_normalized.append(pac_norm)

        # Flatten PAC
        bolt_obj.pac_flat.append( pac.reshape(1,len(pac)*22)[0])
        bolt_obj.pac_flat_normalized.append( pac_norm.reshape(1, len(pac_norm)*22)[0])

    if discard_raw_flag:
        # Clear out raw values - comment out later if they want to be stored
        # Will double the amount of data stored
        del bolt_obj.pdc[:]
        del bolt_obj.electrodes[:]
        del bolt_obj.pac[:]
        del bolt_obj.tdc[:]
        del bolt_obj.tac[:]
        del bolt_obj.pac_flat[:]

    
# Pull from the BoltFeatureObj and return a vector of features and labels
def createFeatureVector(bolt_feature_obj, feature_list):
    """ 
    Given a BoltFeatureObj and a list of features to pull, returns
    the features and labels in vector form for all adjectives

    feature_list: expects a list of strings containing the name of the
                  features to extract
                  
                  Ex. ["max_pdc", "centroid"]

    Returns: Vector of features (1 x feature length)
             Features - in order of feature_list

             Ex. max_pdc = 10, centroid = [14, 10]

             returned numpy array: [10 14 10]

    """
    # Store the features with their adjectives 
    all_feature_vector = list()
   
    # Pull out the features from the object
    for feature in feature_list:
        
        feature_vector = eval('bolt_feature_obj.'+ feature)
        all_feature_vector.append(feature_vector)


    return np.array(all_feature_vector)

# Function to split the data
def split_data(all_bolt_data, train_size):
    """
    Given a dictionary of all bolt objects

    Splits the objects into train and test sets

    train_size is a percentage - Ex. train_size = .9
    """

    train_bolt_data = dict()
    test_bolt_data = dict()
  
    # Calculate train size
    num_runs = len(all_bolt_data[all_bolt_data.keys()[0]])
    train_size = num_runs*train_size
    train_size = int(round(train_size))
    
    # Create list to shuffle and index into objects
    access_idx = range(num_runs)
    shuffle(access_idx)
    access_np_idx = np.array(access_idx)
    
    train_idx = np.nonzero(access_np_idx <= train_size)[0]
    test_idx = np.nonzero(access_np_idx > train_size)[0] 

    # Go through the list of motions
    for motion_name in all_bolt_data:
        motion_list = all_bolt_data[motion_name]

        train_set = [motion_list[i] for i in train_idx]
        test_set = [motion_list[i] for i in test_idx]
 
        train_bolt_data[motion_name] = train_set
        test_bolt_data[motion_name] = test_set
    
    return (train_bolt_data, test_bolt_data)


# Temp place holder function to test extraction
def extract_features(bolt_pr2_motion_obj):
    
    bolt_feature_obj = BoltFeatureObj()

    # Store state information
    bolt_feature_obj.state = bolt_pr2_motion_obj.state
    bolt_feature_obj.detailed_state = bolt_pr2_motion_obj.detailed_state

    # Store phsyical object information
    bolt_feature_obj.name = bolt_pr2_motion_obj.name
    bolt_feature_obj.run_number = bolt_pr2_motion_obj.run_number

    # Store labels in class
    bolt_feature_obj.labels = bolt_pr2_motion_obj.labels

    # PURELY TESTING
    bolt_feature_obj.max_pdc = bolt_pr2_motion_obj.run_number
    bolt_feature_obj.pdc_area = bolt_pr2_motion_obj.run_number

    return bolt_feature_obj
