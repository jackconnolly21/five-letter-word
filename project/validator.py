# necessary to pseudorandomly select a word from the set
import random

# a helper class to more easily validate words,
# as well as only requiring each dictionary to be loaded once
class Validator():
    
    # initialize a instance of the class
    # default dictionary is the full list of five letter words
    def __init__(self, dictionary="dicts/five.txt"):
        
        # initialize a set to store the words
        self.dictionary = set()
        
        # open the dictionary to read from    
        dic = open(dictionary, "r")
        
        # iterate over each line in the dictionary
        for line in dic:
            # remove the new line character
            word = line.strip('\n')
            # append to the set
            self.dictionary.add(word)
    
    # check if a given word is in the dictionary of five letter words    
    def validate(self, word):
        return word in self.dictionary
    
    # returns 1 random word from the set self.dictionary 
    # (used to determine mystery word)   
    def get_mystery(self):
        return random.sample(self.dictionary, 1)[0]