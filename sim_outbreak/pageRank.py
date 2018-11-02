# rank nodes by PageRank score
def pageRank(network):
    
    PRankH = snap.TIntFltH()
    snap.GetPageRank(network, PRankH) # page rank
    PRankH.SortByDat(False) # sort by page rank score
    
    with open("pageRank.txt", "w") as f4:
        for item in PRankH:
            f4.write(str(item) + "\t" + str(PRankH[item]) + "\n")
