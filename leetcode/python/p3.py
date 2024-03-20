#
# @lc app=leetcode.cn id=3 lang=python3
#
# [3] 无重复字符的最长子串
#

# @lc code=start

def first(s: str) -> int:
    unique_list = []
    max_len = 0
    for i in s:
        if i not in unique_list:
            unique_list.append(i)
        else:
            idx = unique_list.index(i)
            unique_list = unique_list[idx+1:]
            unique_list.append(i)

        unique_len = len(unique_list)
        if unique_len > max_len:
            max_len = unique_len
    return max_len


def second(s: str) -> int:
    start = -1
    max_len = 0
    idx_mapping = dict()
    for idx, i in enumerate(s):
        if i in idx_mapping and idx_mapping[i] > start:
            # 字符在字典中,并且位置还在start之后(在start之前的已经不计在最大字符串范围内了,忽略其存在)
            start = idx_mapping[i]
            idx_mapping[i] = idx
            # 如果本次在start之后出现了重复字符,则此次重定位start之后的最大子串长度,肯定是小于以往计算的最大长度
            # 所以无须下列判断覆盖
            # if idx-start > max_len:
            #     max_len = idx-start
        else:
            # 字符不在字典中 或者 在字典中但是位置在start之前
            # 将字符的最新位置更新
            # 如果 最新字符和start之间的最大子串长度大于历史记录的最大长度,则替换最大长度
            idx_mapping[i] = idx
            if idx-start > max_len:
                max_len = idx-start
    return max_len


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        # return first(s)
        return second(s)


# @lc code=end
