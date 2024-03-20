#
# @lc app=leetcode.cn id=2 lang=python3
#
# [2] 两数相加
#
from typing import Optional
# @lc code=start
# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next


def first(l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
    if l1.val == None and l2.val == None:
        return None
    cur_l1_v = l1.val
    cur_l2_v = l2.val
    result_link_list = last_link_node = ListNode()
    carry = 0
    while True:
        if cur_l1_v == None and cur_l2_v == None:
            break
        cur_total = (cur_l1_v or 0) + (cur_l2_v or 0) + carry
        stay = cur_total

        if cur_total >= 10:
            stay = cur_total-10
            carry = 1
        else:
            carry = 0

        last_link_node.next = ListNode(stay)
        last_link_node = last_link_node.next

        l1 = l1.next if l1 else None
        l2 = l2.next if l2 else None
        cur_l1_v = None if l1 == None else l1.val
        cur_l2_v = None if l2 == None else l2.val

    if carry == 1:
        last_link_node.next = ListNode(1)
    return result_link_list.next


def second(l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
    current_node = ListNode()  # 链表初始标记节点
    mark_node = current_node
    carry = 0
    while l1 or l2 or carry:
        l1_cur_v = l1.val if l1 else 0
        l2_cur_v = l2.val if l2 else 0
        cur_total = l1_cur_v + l2_cur_v + carry
        stay_node = ListNode(cur_total % 10)
        current_node.next = stay_node
        current_node = stay_node
        carry = cur_total // 10  # cary //= 10
        l1 = l1.next if l1 else None
        l2 = l2.next if l2 else None
    return mark_node.next


def third(l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
    def recursion(first, second, carry):
        if not first and not second and carry == 0:
            return None
        l1_cur_v = first.val if first else 0
        l2_cur_v = second.val if second else 0
        total = l1_cur_v + l2_cur_v + carry
        stay_node = ListNode(total % 10)
        stay_node.next = recursion(first.next if first else None, second.next if second else None, total // 10)
        return stay_node
    return recursion(l1, l2, 0)


class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:

        # return first(l1, l2)
        # return second(l1, l2)
        return third(l1, l2)

# @lc code=end
