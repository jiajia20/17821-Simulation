import networkx as nx
import random as rd
import numpy as np
import pandas as pd

alpha = 2 # threeshold for passing message
omega = 2 #thresgold for stance flip

############# Sec-1 Two object, agent and msg ###################
class agent:
    def __init__(self, i, vulunerability = True, stance = 1):
        self.stance = stance # 1 is pro, -1 is anti
        self.vulunerable = vulunerability
        self.index = i
        self.associated_msg = [] #list of index for associated message 

    def stance_flip(self):
        self.stance = self.stance * (-1)

    def get_msg(self, new_msg):
        self.associated_msg.append(new_msg)

    def purge_msg(self):
        new_msg_list = []
        for msg in self.associated_msg:
            if msg.freshness > 0:
                new_msg_list.append(msg)
        new_msg_no_rep = list(set(new_msg_list))  
        #currently does not purge repeated msg because one can see multiple RT of same msg
        #PURGE repeated msg for practical reason, otherwise msg explode
        self.associated_msg = new_msg_no_rep

    def calculate_msg(self):
        SE, SL, DE, DL = [0,0,0,0]
        if len(self.associated_msg) > 0:
            for message in self.associated_msg:
                if message.freshness > 0:
                    if message.stance == self.stance and message.manuver == 'E':
                        SE += 1
                    elif message.stance == self.stance and message.manuver == 'L':
                        SL += 1
                    elif message.stance != self.stance and message.manuver == 'E':
                        DE += 1
                    elif message.stance != self.stance and message.manuver == 'L':
                        DL += 1
        return(SE, SL, DE, DL)


class msg:
    def __init__(self,i, manuver, stance = 1):  # 1 is pro, -1 is anti
        self.index = i
        self.stance = stance
        self.manuver = manuver # E - emotional L - logical
        self.freshness = 3 # start from 3

    def msg_age(self):
        if self.freshness >0:
            self.freshness -= 1


############# Sec-2 basic function, generate news and spread msg ###################

def news_generate(network, agent_dict, msg_list, news_agent_index, message_index, manuver, stance):
    #generate new message
    # i is the index for 
    new_msg = msg(message_index,manuver, stance)

    # add msg to list to keep track of aging of msg
    msg_list.append(new_msg)

    #get neighbor
    neighbors = [n for n in network.neighbors(news_agent_index)] #list of index for neighbors
    for j in neighbors:
        agent = agent_dict.get(j)
        agent.get_msg(new_msg)




def singe_agent_spread(network,agent_dict, agent, alpha = alpha, omega = omega):
    SE, SL, DE, DL = agent.calculate_msg()
    neighbors = [n for n in network.neighbors(agent.index)]
    threshold = 0 
    flip_thresold = 0 
    if agent.vulunerable == False:
        threshold = SE + SL - (DE + DL)
        flip_thresold = (DE + DL) - (SE + SL)
    else:
        threshold = 2*SE + SL - (0*DE + DL) 
        flip_thresold =  (0*DE + DL) - (2*SE + SL)
    
    # print('agent',agent.index ,'threshold:', threshold, ', flip:', flip_thresold)
    if threshold > alpha and len(agent.associated_msg)>0:
        # print('spread')
        for msg  in agent.associated_msg:
            #spread only new fresh msg that have the samce stance
            if msg.freshness > 0 and msg.stance == agent.stance:
                # print('msg ' + str(msg.index) + ' frensh and spreading')
                for j in neighbors:
                    msg_receiver = agent_dict[j]
                    # print(j, msg_receiver) 
                    if j > 1:
                    #type(agent_dict[j]) == type(agent): 
                        """ THIS IS WIRED PROBLEM """
                        # print(' to agent ' + str(msg_receiver.index))
                        agent_dict[j].get_msg(msg)
                        

    if flip_thresold > omega:
        # print('flip')
        agent.stance_flip()

### Additional function, age msg and purge msg to avoid excess msg ############
def age_msg(msg_list):
    for msg in msg_list:
        msg.msg_age()

def purge_all_agent_msg(agent_dict):
    for i in agent_dict:
        if i > 1:
        #type(agent_dict[i]) == agent:
            agent_dict[i].purge_msg()



############# Sec-3 intialization, time step and data capture:  ###################
def intialize_agent(agent_num, pct_vul, p=0.4):
    """
    agent_num: numbers of agent
    pct_vul: percentage of vulunerable agents in fraction (e.g 0.5)
    p: probability of a edge between two nodes - for network
    # seed: random seed - for network
    not coded - agent stance 50% pro 50% against
    """
    agent_dict = {}
    #default first two agent to be news
    agent_dict.update({0: 'news_0, +1'}) 
    agent_dict.update({1: 'news_1, -1'})

    for index in range(2,agent_num):
        vul = (rd.random() < pct_vul)
        stc = rd.choice([-1,1])
        new_agent = agent(i= index, vulunerability = vul, stance = stc)
        agent_dict.update({index:new_agent})

    return(G, agent_dict)

def initialize_agent_data(agent_num):
    """
    initialize the data collection, output two empty pandas df with index
    """
    index_list = [n for n in range(agent_num)]
    df_stance = pd.DataFrame(columns = index_list )
    df_msgNum = pd.DataFrame(columns = index_list )
    return(df_stance, df_msgNum)

def agent_snap_shot(agent_dict):
    """ 
    input agent_dict, output two list of agent's current stance and number of msh
    can implement to present content of such msg too
    """
    stance_list= []
    associated_msg_len_list = []
    for i in agent_dict:
        if i == 0:
            stance_list.append(1)
            associated_msg_len_list.append(np.NaN)
        elif i == 1:
            stance_list.append(-1)
            associated_msg_len_list.append(np.NaN)
        else:
            stance_list.append(agent_dict[i].stance)
            associated_msg_len_list.append(len(agent_dict[i].associated_msg))

    return(stance_list,associated_msg_len_list)

def update_df(agent_dict, df_stance, df_msg):
    """ 
    take global variable agent_dict, df_stance, df_msg
    add a row after each time step
    """
    stance_l, msg_l_l = agent_snap_shot(agent_dict)
    df_stance.loc[len(df_stance)] = stance_l
    df_msg.loc[len(df_stance)] = msg_l_l


def time_step(G, agent_dict,msg_list, msg_index, manuver_pct_E, df_stance, df_msg):
    """
    G: networkX network object
    agent_dict: dictionary of agent, first twi (0,1) is news agent
    msg_list: global variable of message, used for aging msg
    msg_index: index for the new msg, should be i in some loop
    manuver_pct_E: percent chance of a msg using Emotion as focus
    """
    #generate news
    stance = lambda pct: 'E' if (rd.random() <pct) else 'L' 
    stance_news_0 = stance(manuver_pct_E)
    stance_news_1 = stance(manuver_pct_E)
    news_generate(G,agent_dict, msg_list, news_agent_index = 0, message_index = msg_index, manuver = stance_news_0, stance = 1)
    news_generate(G,agent_dict, msg_list, news_agent_index = 1, message_index = msg_index, manuver = stance_news_1, stance = -1)

    order_l = [n for n in range(len(agent_dict))]
    rd.shuffle(order_l) 
    
    #then make agent spread the news
    for i in order_l:
        if (i !=0) and (i != 1):
            singe_agent_spread(G, agent_dict, agent_dict[i])

    #age the msg and purge agent associated msg list
    age_msg(msg_list)
    purge_all_agent_msg(agent_dict)

    #take snapshot
    update_df(agent_dict, df_stance, df_msg)