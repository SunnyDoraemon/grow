#
# @lc app=leetcode.cn id=1 lang=python3
#
# [1] 两数之和
#
# @lc code=start
from typing import List


def first(nums: List[int], target: int) -> List[int]:
    for idx, item in enumerate(nums):
        aim = target-item
        try:
            aim_index = nums.index(aim, idx+1)
        except:
            aim_index = -1
        if aim_index != -1:
            return [idx, aim_index]
        else:
            return []


def second(nums: List[int], target: int) -> List[int]:
    d = dict()
    for idx, item in enumerate(nums):
        if target-item in d:
            return [idx, d[target-item]]
        d[item] = idx
    return []


class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        # return first(nums, target)
        return second(nums, target)
# @lc code=end


print(first([3, 4], 6))

# >>> python list调查
l = [1, 3, 4, 5]
l.reverse()
print(l)
