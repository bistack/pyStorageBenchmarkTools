#!/usr/bin/python
'''Filename: crossbar_ldpc.py
Author: Sun Zhenyuan <sunzhenyuan@163.com> 2015.05 '''

# input the count of total data nodes, the degree of redundency

import math
import random

class Data_Node:
    def __init__(self, vol_idx):
        self.matrix_vol = list()
        self.vol_idx = vol_idx
        self.__redundency_degree = 0

    def init_row(self, row_idx):
        while len(self.matrix_vol) <= row_idx:
            self.matrix_vol.append(0)

    def set_row(self, row_idx):
        if not self.matrix_vol[row_idx]:
            self.matrix_vol[row_idx] = 1
            self.__redundency_degree += 1

    def get_row(self, row_idx):
        if row_idx >= len(self.matrix_vol):
            return 0

        return self.matrix_vol[row_idx]
    
    def clear_row(self, row_idx):
        if self.matrix_vol[row_idx]:
            self.matrix_vol[row_idx] = 0
            self.__redundency_degree -= 1

        if not self.__redundency_degree:
            return 1
        else:
            return 0
        
    def get_redundency_degree(self):
        return self.__redundency_degree

class Parity_Node:
    def __init__(self, row_idx):
        self.__row_idx = row_idx
        self.__data_node_cnt = 0

    def inc_data_node_cnt(self):
        self.__data_node_cnt += 1

    def dec_data_node_cnt(self):
        if not self.__data_node_cnt:
#            print "parity %d has no data node to delete" % (self.__row_idx)
            return 1

        self.__data_node_cnt -= 1
        
        if not self.__data_node_cnt:
            return 1
        else:
            return 0

    def get_data_node_cnt(self):
        return self.__data_node_cnt


class Crossbar_Ldpc:
    def __init__(self, redundency_degree, target_node_cnt):
        self.__data_matrix = list()
        self.__parity_vol = list()
        self.__redundency_degree = redundency_degree
        self.__target_node_cnt = target_node_cnt

    def is_target_far(self):
        data_cnt = len(self.__data_matrix)
        if not data_cnt:
            return -1

        parity_cnt = len(self.__parity_vol)
        if not parity_cnt:
            return -1

        node_cnt = data_cnt + parity_cnt
        
        if node_cnt > self.__target_node_cnt + self.__redundency_degree:
            return 1
        elif node_cnt < self.__target_node_cnt - self.__redundency_degree:
            return -1
        else:
            return 0

    def __alloc_data_matrix(self):
        for i in range(self.__target_node_cnt):
            data_node = Data_Node(i)
            self.__data_matrix.append(data_node)

    def __free_data_matrix(self):
        cnt = len(self.__data_matrix)
        while cnt > 0:
            del self.__data_matrix[cnt-1]
            cnt = len(self.__data_matrix)

    def __alloc_parity_node(self, row_idx):
        parity_node = Parity_Node(row_idx)
        self.__parity_vol.append(parity_node)

    def __free_parity_vol(self):
        cnt = len(self.__parity_vol)
        while cnt > 0:
            del self.__parity_vol[cnt-1]
            cnt = len(self.__parity_vol)

    def print_encode_matrix(self):
        print ("target node cnt %d, redundency degree %d "
               "data node cnt %d parity node cnt %d"
               % (self.__target_node_cnt, self.__redundency_degree,
                  len(self.__data_matrix), len(self.__parity_vol)))
        for row_idx in range(len(self.__parity_vol)):
            for vol_idx in range(len(self.__data_matrix)):
                if self.__data_matrix[vol_idx].get_row(row_idx):
                    print '1',
                else:
                    print '0',
            print

    def __mark_row_by_space(self, row_idx, start_vol_idx,
                            space, group_width):

        for i in range(group_width):
            vol_idx = start_vol_idx + i * space
            if vol_idx >= len(self.__data_matrix):
                break
            self.__data_matrix[vol_idx].init_row(row_idx)
            self.__data_matrix[vol_idx].set_row(row_idx)

            parity_idx = len(self.__parity_vol)
            while parity_idx <= row_idx:
                self.__alloc_parity_node(parity_idx)
                parity_idx = len(self.__parity_vol)

            self.__parity_vol[row_idx].inc_data_node_cnt()

    def create_rc_ldpc(self, group_width):
        self.__alloc_data_matrix()
        data_cnt = len(self.__data_matrix)
        group_cnt = int((data_cnt + group_width - 1)
                        / group_width)
            
        row_idx = 0

        for x in range(self.__redundency_degree):
            space = int(math.pow(group_width, x))

            group_idx = 0
            while group_idx < data_cnt:
                vol_idx = group_idx

                while vol_idx < group_idx + space:
                    self.__mark_row_by_space(row_idx, vol_idx, space, group_width)
                    row_idx += 1
                    vol_idx += 1

                group_idx += space * group_width
            
        """
        print ("RC_LDPC: data node count %d, parity node count %d\n"
               "\t redundency degree %d, group width %d, group cnt %d"
               % (len(self.__data_matrix), len(self.__parity_vol),
                  self.__redundency_degree, group_width,
                  group_cnt))
        self.print_encode_matrix()
        """
        self.check_ldpc()

    def check_ldpc(self):
        parity_cnt = len(self.__parity_vol)
        data_cnt = len(self.__data_matrix)
        for vol_idx in range(data_cnt):
            data_node = self.__data_matrix[vol_idx]

            if len(data_node.matrix_vol) > parity_cnt:
                print ("vol %d data %d > %d"
                       % (vol_idx, len(data_node.matrix_vol), parity_cnt))
                print data_node.matrix_vol
                self.print_encode_matrix()

            assert len(data_node.matrix_vol) <= parity_cnt
        
        for row_idx in range(parity_cnt):
            parity_node = self.__parity_vol[row_idx]
            row_data_cnt = 0

            for vol_idx in range(data_cnt):
                data_node = self.__data_matrix[vol_idx]
                if data_node.get_row(row_idx):
                    row_data_cnt += 1

            if row_data_cnt != parity_node.get_data_node_cnt():
                print "row %d" % (row_idx)
                for vol_idx in range(data_cnt):
                    data_node = self.__data_matrix[vol_idx]
                    if data_node.matrix_vol[vol_idx]:
                        print '1',
                    else:
                        print '0',
                print
                self.print_encode_matrix()

            assert row_data_cnt == parity_node.get_data_node_cnt()

    def __del_parity_node(self, row_idx):
        if len(self.__parity_vol) <= row_idx:
            print ("wrong parity index %d, has %d"
                   % (row_idx, len(self.__parity_vol)))
            return

        del self.__parity_vol[row_idx]


    def __del_data_node(self, vol_idx):
        if len(self.__data_matrix) <= vol_idx:
            print ("wrong data index %d, has %d"
                   % (vol_idx, len(self.__data_matrix)))
            return

        del self.__data_matrix[vol_idx]
        

    def del_data_node(self, vol_idx):
        self.check_ldpc()
        empty = 1
        data_node = self.__data_matrix[vol_idx]
        row_idx = len(data_node.matrix_vol)

        while row_idx:
            row_idx -= 1

            if data_node.get_row(row_idx):
                if row_idx >= len(self.__parity_vol):
                    print data_node.matrix_vol
                    print "row %d" % (row_idx)

                assert row_idx < len(self.__parity_vol)

                empty = data_node.clear_row(row_idx)
                parity_node = self.__parity_vol[row_idx]
                if parity_node.dec_data_node_cnt():
                    self.del_parity_node(row_idx)

        assert empty
        self.__del_data_node(vol_idx)
        self.check_ldpc()

    def del_parity_node(self, row_idx):
        vol_idx = len(self.__data_matrix)
        empty = 1

        while vol_idx:
            vol_idx -= 1
            data_node = self.__data_matrix[vol_idx]
            data_zero = 0
            if data_node.get_row(row_idx):
                data_zero = data_node.clear_row(row_idx)
                empty = self.__parity_vol[row_idx].dec_data_node_cnt()            

            if row_idx < len(data_node.matrix_vol):
                del data_node.matrix_vol[row_idx]

            if data_zero:
                self.__del_data_node(vol_idx)                

        assert empty
        self.__del_parity_node(row_idx)
        self.check_ldpc()

    def find_min_parity_row(self):
        parity_cnt = len(self.__parity_vol)
        min_row = parity_cnt
        min_cnt = len(self.__data_matrix)
        max_cnt = 0

        for row_idx in range(parity_cnt):
            parity_node = self.__parity_vol[row_idx]
            cnt = parity_node.get_data_node_cnt()

            if cnt < min_cnt:
                min_cnt = cnt
                min_row = row_idx

            if cnt > max_cnt:
                max_cnt = cnt

        if max_cnt <= min_cnt:
            min_row = parity_cnt

        return min_row

    def find_min_data_vol(self):
        data_cnt = len(self.__data_matrix)
        min_vol = data_cnt
        min_redundency = self.__redundency_degree

        for vol_idx in range(data_cnt):
            data_node = self.__data_matrix[vol_idx]
            cnt = data_node.get_redundency_degree()

            if cnt < min_redundency:
                min_vol = vol_idx
                break

        return min_vol

    def __reduce_node(self, use_rand=1):
        while True:
            reduced = 0
            
            min_data_vol = self.find_min_data_vol()
            while min_data_vol < len(self.__data_matrix):
                self.del_data_node(min_data_vol)
                """
                if not len(self.__parity_vol):
                    break
                """
                min_data_vol = self.find_min_data_vol()
                reduced = 1
            
            far = self.is_target_far()
            if far <= 0:
                return far

            if not use_rand:
                min_parity_row = self.find_min_parity_row()
                if min_parity_row < len(self.__parity_vol):
                    self.del_parity_node(min_parity_row)
                    reduced = 1

            if not reduced or use_rand:
                if random.randint(0, 1):
                    data_vol = random.randint(0, len(self.__data_matrix) - 1)
                    self.del_data_node(data_vol)
#                    print "try reduce data node %d" % (data_vol)
                else:
                    parity_row = random.randint(0, len(self.__parity_vol) - 1)
                    self.del_parity_node(parity_row)
#                    print "try reduce parit node %d" % (parity_row)
        

    def find_gc_ldpc(self):
        width = (int(math.log(self.__target_node_cnt,
                              self.__redundency_degree)) + 1) * 2

        while width >= 2:
            #print "try width %d" % (width)
            self.create_rc_ldpc(width)

            if len(self.__data_matrix[0].matrix_vol) > len(self.__parity_vol):
                print ("%d %d"
                       % (len(self.__data_matrix[0].matrix_vol),
                          len(self.__parity_vol)))

            assert len(self.__data_matrix[0].matrix_vol) <= len(self.__parity_vol)

            far = self.__reduce_node()

            if far < 0:
                width -= 1
                self.__free_parity_vol()
                self.__free_data_matrix()
            else:
                break

#        self.print_encode_matrix()

    def efficiency(self):
        data_cnt = len(self.__data_matrix)
        if not data_cnt:
            return float(0)

        parity_cnt = len(self.__parity_vol)
        if not parity_cnt:
            return float(1)

        return float(data_cnt) / float((data_cnt + parity_cnt))

for i in range(2, 5):
    for j in range(3, 21):
        max_effi = float(1) / float(1+i)
        for t in range(10000):
            c_ldpc = Crossbar_Ldpc(i, j)
            c_ldpc.find_gc_ldpc()
            effi = c_ldpc.efficiency()

            if effi > max_effi:
                max_effi = effi
                print effi
                c_ldpc.print_encode_matrix()
