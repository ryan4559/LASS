# @file model.py
# @brief the sample file that copied for new python file
# README: Simulation core related
# MODULE_ARCH:  
# CLASS_ARCH:
# GLOBAL USAGE: 
#standard
import logging
import random
import math
from datetime import datetime,timedelta
#extend
#library
import lib.globalclasses as gc
from lib.const import *
from codes.lassdata import *
import lib.util as util

##### Code section #####
### Producer section of model 
#Spec: One factory entity
#How/NeedToKnow:
class Factory():
    def __init__(self,name,x,y):
        self.pos_x = x
        self.pos_y = y 
        self.name = name
#Spec: Entity base that should be used in all entities
#How/NeedToKnow:
class EntityBase():
    def __init__(self):
        self.process_count = 1

#Spec: Manager alll factory information
#How/NeedToKnow:        
class FactoryMgr(EntityBase):
    def __init__(self):
        self.process_count = 1
        self.ents = {} #factory list in dictionary, index by name
        self.init_test()
    def init_test(self):
        factory = Factory("test_factory",5,5)
        self.ents[factory.name] = factory
### Status section of model 
#Spec: The base unit in the map
#How/NeedToKnow:
class Position():
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.pm_total = 0.0 
        self.pm_value = 0.0       
        self.base = 10000.0 #TBD
        self.wind_dir = 0.0 #clockwise degree, north(0)
        self.wind_speed = 0.0 # m/s
        self.wind_pm_offset =0.0 #the calculated pm offset that should updated in the end of process
        pass
    def total_to_value(self):
        self.pm_value = self.pm_total/self.base
    def value_to_total(self):
        self.pm_total = self.pm_value * self.base
    def wind_set(self,wind_dir,wind_speed):
        self.wind_dir = wind_dir
        self.wind_speed = wind_speed
    #calculate offset(%) and return to caller, add to another position
    def set_pm_offset(self,offset_p): #offset is % that will move out. 0-1
        offset = -(self.pm_total * offset_p)
        self.wind_pm_offset += offset 
        return offset
    def update_pm_offset(self):
        self.pm_in(self.wind_pm_offset)
        self.wind_pm_offset=0.0
    def pm_in(self,amount):
        self.pm_total += amount
        self.total_to_value()
    def pm_set(self,amount):
        self.pm_value = amount
        self.value_to_total()
        
#Spec: The map that record the status of that moment
#How/NeedToKnow:
class Map():
    def __init__(self):
        self.poss = {} # dict of all positions, index = x@y, x start from 0, y start from 0
        
        self.x0 = float(gc.SETTING["XLL_CORNER"]) #120.13125 
        self.y0 = float(gc.SETTING["YLL_CORNER"])#23.38125

        self.x1 = float(gc.SETTING["XLL_CORNER1"]) #120.13125 
        self.y1 = float(gc.SETTING["YLL_CORNER1"])#23.38125
        
        self.cellsize = float(gc.SETTING["CELL_SIZE"])#0.0125
        [x,y] = self.gps_to_idx([self.x1,self.y1])
        self.x_max = int(x)+1
        self.y_max = int(y)+1
        
        #self.x_max = int(gc.SETTING["X_MAX"]) #10 # 0-x_max
        #self.y_max = int(gc.SETTING["Y_MAX"])#10 # 0-y_max

        self.nodata_value = 0
        
        self.timestamp = None #datetime object
        
        
        self.init()
        
    def init(self):
        for x in range(0,self.x_max):
            for y in range(0,self.y_max):
                pos_idx = "%i@%i" % (x,y) 
                self.poss[pos_idx] = Position(x,y)
    def gps_to_idx(self,gps): #gps: [long,lat], return [x,y]
        x = util.distance_by_geo(self.x0,self.y0,gps[0],self.y0)
        idx_x = int(x/self.cellsize) 
        y = util.distance_by_geo(self.x0,self.y0,self.x0,gps[1])
        idx_y = int(y/self.cellsize)
        return [idx_x,idx_y] 
        #pos_idx = "%i@%i" % (x,y)
        #return pos_idx
    def pos_inout(self,x,y,amount): # minus amount is out 
        pos_idx = "%i@%i" % (x,y) 
        self.poss[pos_idx].pm_in(amount) 
    def get_random_pos(self):
        pos_offset = random.randint(0, self.x_max * self.y_max -1)
        y = int(pos_offset / self.y_max)
        x = pos_offset % self.y_max
        pos_idx = "%i@%i" % (x,y) 
        return self.poss[pos_idx]
    def all_inout(self,amount): # all pos minus amount
        for x in range(0,self.x_max):
            for y in range(0,self.y_max):
                pos_idx = "%i@%i" % (x,y) 
                self.poss[pos_idx].pm_in(amount)        
    def process_wind(self):
        #prepare for update
        for x in range(0,self.x_max):
            for y in range(0,self.y_max):
                pos_idx = "%i@%i" % (x,y) 
                offset = self.poss[pos_idx].set_pm_offset(0.2) # FIXME
                #print("Offset=%f" %(offset))
                if x < self.x_max-1:
                    pos_idx_new = "%i@%i" % (x+1,y)
                    self.poss[pos_idx_new].wind_pm_offset -=offset

        for x in range(0,self.x_max):
            for y in range(0,self.y_max):
                pos_idx = "%i@%i" % (x,y) 
                self.poss[pos_idx].update_pm_offset()
        
    def sum_pm_total(self):
        pm_total = 0
        for x in range(0,self.x_max):
            for y in range(0,self.y_max):
                pos_idx = "%i@%i" % (x,y) 
                pm_total += self.poss[pos_idx].pm_total       
        self.pm_total = pm_total
    
    def desc(self):
        str = "Map Descriptor:\nCurrent positions count = %i\n" % (len(self.poss))
        for y in range(0,self.y_max):
            for x in range(0,self.x_max):
                pos_idx = "%i@%i" % (x,y)
                str1 = "\t%f" % (self.poss[pos_idx].pm_value)
                str += str1
            str += "\n"
        return str

#Spec: Monitor the model, collect the history
#How/NeedToKnow:
class ModelMonitor():
    def __init__(self):
        self.pm_total=[]
        self.pm_map_diffs = []
        pass
    def mon_step(self,pm_total,map_diff):
        self.pm_total.append(pm_total)
        self.pm_map_diffs.append(map_diff)
#Spec: Core simulation model
#How/NeedToKnow:
class Model():
    def __init__(self,env):
        #private
        #global: these variables allow to direct access from outside.
        self.env = env
        self.map = None # model's map
        self.map_prev = None # prev map of last time unit
        #self.lassdata = None # lassdata(LassDataMgr)
        self.desc_list=[] # some description about the model
        
        self.factory_mgr = None #factory_mgr(FactoryMgr) 
        
        fmt = '%Y-%m-%d %H:%M:%S'
        if "MODEL_START_TIME" in gc.SETTING:
            self.dt_start = datetime.strptime(gc.SETTING["MODEL_START_TIME"], fmt)
        else:
            tmp_now = datetime.now()
            hour_time = datetime( tmp_now.year, tmp_now.month, tmp_now.day, tmp_now.hour )
            self.dt_start = hour_time + timedelta(days=-2) + timedelta(hours=-8) # temp for using GMT0
        self.dt_end = self.dt_start #init value
        self.corners = [float(gc.SETTING["XLL_CORNER"]),float(gc.SETTING["YLL_CORNER"]),float(gc.SETTING["XLL_CORNER1"]),float(gc.SETTING["YLL_CORNER1"])]
        #process enable configuration, 0-disable, 1-enable
        self.proc_enabled={'deposition':0,'windset':0,'wind':0,'population':0,'factory':0,'align_lass':1}
        self.count_population=5 # process count of population_run
        self.count_car=2 # process count of car_run
        self.init()
        
    def init(self):
        self.map = Map() 
        self.map.timestamp = self.dt_start
        
        self.factory_mgr = FactoryMgr()
        #self.lassdata = LassDataMgr()
    
    def entity_setup(self):
        if self.proc_enabled['deposition']:
            self.desc_list.append("1* deposition -10 every time unit.")
            self.env.process(self.deposition_run()) 
        if self.proc_enabled['windset']:
            self.desc_list.append("1* windset setup wind every 10 time unit.")
            self.env.process(self.windset_run()) 
        if self.proc_enabled['wind']:
            self.desc_list.append("1* wind process every time unit.")
            self.env.process(self.wind_run()) 
        if self.proc_enabled['align_lass']:
            self.desc_list.append("1* align_lass set every hour." )
            self.env.process(self.align_lass_run())  
                    
        if self.proc_enabled['population']:
            self.desc_list.append("%i* population +1 every time unit." %(self.count_population))
            for i in range(0,self.count_population):
                self.env.process(self.population_run())  

        if self.proc_enabled['factory']:
            self.desc_list.append("1* factory +10 at (5,5)." )
            for i in range(0,self.factory_mgr.process_count):
                self.env.process(self.factory_run())  


        
        #self.desc_list.append("%i* car +1000 when minute mode 3 ==0." %(self.count_car))
        #for i in range(0,self.count_car):
        #    self.env.process(self.car_run())  
        
        
    # now unit is minute, 
    def now_to_datetime(self):
        return self.dt_start +timedelta(minutes=self.env.now)

    def deposition_run(self):
        while True:
            self.map.all_inout(-10)
            print(self.now_to_datetime())
            yield self.env.timeout(1)

    def align_lass_run(self): #time unit hour
        while True:
            gc.LASSDATA.apply_to_map(self.map,self.map.timestamp,"default")
            #apply to map
            yield self.env.timeout(1)

    #setup wind direction every x min
    def windset_run(self):
        while True:
            wind_dir = 90
            wind_speed = 10
            for x in range(0,self.map.x_max):
                for y in range(0,self.map.y_max):
                    pos_idx = "%i@%i" % (x,y) 
                    self.map.poss[pos_idx].wind_set(wind_dir,wind_speed)        

            yield self.env.timeout(10)
    def wind_run(self):
        while True:
            self.map.process_wind()
            yield self.env.timeout(1)           
    def car_run(self):
        while True:
            #print('Now at %d' % self.env.now)
            pos = self.map.get_random_pos()
            dt_now = self.now_to_datetime()
            if dt_now.minute % 3 ==0:
                pos.pm_in(1000)
                
            yield self.env.timeout(1)
    def factory_run(self):
        while True:
            for key in self.factory_mgr.ents.keys():
                factory = self.factory_mgr.ents[key]
                pos_idx = "%i@%i" % (factory.pos_x,factory.pos_y) 
                self.map.poss[pos_idx].pm_in(100)        
            yield self.env.timeout(1)
    
    
    def population_run(self):
        while True:
            self.map.all_inout(10)
            
            yield self.env.timeout(1)
    #to evaluate 1 map result
    #Argorithm = by each sensor location, average of (fact-sim)
    def map_evaluation(self,map_sim,map_fact,lassdata): # lassdata have device index list
        #get pos_idx list
        pos_idxs = lassdata.get_posidx_by_tag("default")
        sum_value_diff = 0.0
        map_valid = False #need to check if map_sim, map_fact should have data
        for pos_idx in pos_idxs:
            if map_fact.poss[pos_idx].pm_value>0 and map_sim.poss[pos_idx].pm_value>0:
                map_valid = True
            sum_value_diff += math.fabs(map_fact.poss[pos_idx].pm_value - map_sim.poss[pos_idx].pm_value)
        avg_value_diff = sum_value_diff / len(pos_idxs)
        if map_valid:
            return avg_value_diff
        else:
            return 0.0
    def get_desc_str(self):
        return "\n".join(self.desc_list)   
    def desc(self):
        return self.map.desc()
