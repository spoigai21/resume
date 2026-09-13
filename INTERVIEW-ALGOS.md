# Technical Interview — Algorithms

Every snippet here was executed against the standard cases before being written down.
Python, because it has the least syntax overhead under time pressure.

**Drill order:** two pointers → hashing → sliding window → binary search → sorting →
prefix/Kadane → linked lists → matrix/strings → stack.

---

## Pattern recognition — the first sixty seconds

The round is decided by picking the right family before you write anything.

| Signal in the problem | Reach for |
|---|---|
| Input is **sorted**, or sorting it is free | Two pointers converging, or binary search |
| Pair / triplet summing to a target | Sorted → converge. Unsorted pairs → hash complement |
| **"In place"** or `O(1)` space required | Read/write two pointers (the constraint exists to ban the hash solution) |
| Contiguous subarray/substring, **all positive** | Sliding window |
| Contiguous subarray/substring, **negatives present** | Prefix sum + hash — the window breaks |
| **Count** subarrays with a property | Prefix sum + hash |
| Max/min subarray sum | Kadane |
| "Smallest X that works", with a monotone check | Binary search on the answer |
| Overlapping ranges / meetings / schedules | Sort by start, then sweep |
| "Next greater / next smaller" | Monotonic stack |
| Top k / k most frequent | Bucket by count (`O(n)`) or heap (`O(n log k)`) |
| Group items sharing a property | Canonical key into a dict |
| Longest run of consecutive values | Set + run-head guard |
| Matching brackets, undo, nesting | Stack |

**Two questions to ask out loud before coding:**
1. *"Are all the values positive?"* — on any subarray problem. This is the actual fork
   between sliding window and prefix sums, and asking it unprompted is the strongest
   signal you can send.
2. *"Can I modify the input?"* — decides whether sorting in place is allowed.

Then state the approach and **both complexities before typing**.

---

## 1. Two pointers

### Converging on sorted input
A failed pair eliminates one element permanently — that's why it's `O(n)`, not `O(n²)`.

```python
def two_sum_sorted(a, target):
    lo, hi = 0, len(a) - 1
    while lo < hi:
        s = a[lo] + a[hi]
        if s == target: return (lo, hi)
        if s < target:  lo += 1        # only way to increase the sum
        else:           hi -= 1        # only way to decrease it
    return None
```
`O(n)` time, `O(1)` space.

### Converging with greedy discard
The one interviewers push hardest on. **The argument:** area is bounded by the *shorter*
side, so moving the taller pointer inward shrinks the width and cannot raise the min —
it can never improve. Discard the shorter side.

```python
def max_area(h):
    lo, hi, best = 0, len(h) - 1, 0
    while lo < hi:
        best = max(best, (hi - lo) * min(h[lo], h[hi]))
        if h[lo] < h[hi]: lo += 1
        else:             hi -= 1
    return best
```

### Read/write — in-place modification
Invariant: `a[:w]` is the finished answer at every moment. `r` scans, `w` commits.

```python
def move_zeroes(a):
    w = 0
    for r in range(len(a)):
        if a[r] != 0:
            a[w], a[r] = a[r], a[w]; w += 1
    return a

def dedupe_sorted(a):                  # returns new length, mutates in place
    if not a: return 0
    w = 1
    for r in range(1, len(a)):
        if a[r] != a[w - 1]:
            a[w] = a[r]; w += 1
    return w
```

### Three-way partition (Dutch flag)
Three buckets in one pass.

```python
def sort_colors(a):
    lo, i, hi = 0, 0, len(a) - 1
    while i <= hi:
        if   a[i] == 0: a[lo], a[i] = a[i], a[lo]; lo += 1; i += 1
        elif a[i] == 2: a[hi], a[i] = a[i], a[hi]; hi -= 1   # i does NOT advance
        else:           i += 1
```
**The bug that kills you:** after swapping in from the `hi` end you haven't examined what
arrived, so `i` must not advance. Most-watched mistake in this problem.

### Fix one, converge on the rest
```python
def three_sum(nums):
    nums.sort(); res = []; n = len(nums)
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]: continue    # dup skip 1: the anchor
        if nums[i] > 0: break                            # prune
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = nums[i] + nums[lo] + nums[hi]
            if   s < 0: lo += 1
            elif s > 0: hi -= 1
            else:
                res.append([nums[i], nums[lo], nums[hi]])
                lo += 1; hi -= 1
                while lo < hi and nums[lo] == nums[lo - 1]: lo += 1   # dup skip 2
    return res
```
`O(n²)`. **Duplicate skipping is needed in two places** — the outer anchor and after a
hit. Missing either produces duplicate triplets.

### Merge sorted array in place — fill from the back
```python
def merge_into(a, m, b, n):            # a has m real values + n empty slots
    i, j, w = m - 1, n - 1, m + n - 1
    while j >= 0:
        if i >= 0 and a[i] > b[j]: a[w] = a[i]; i -= 1
        else:                      a[w] = b[j]; j -= 1
        w -= 1
    return a
```
Writing forward would overwrite unread values. Backward is the whole trick.

---

## 2. Hash maps

### Complement lookup
```python
def two_sum(a, target):
    seen = {}
    for i, v in enumerate(a):
        if target - v in seen: return (seen[target - v], i)   # check BEFORE insert
        seen[v] = i
```
**The bug:** insert before checking and an element pairs with itself when the target is
double its value.

### Prefix sum + hash — when negatives break the window
A subarray's sum is the difference of two prefix sums. Subarrays ending here that sum to
`k` = how many earlier prefix sums equalled `running - k`.

```python
from collections import defaultdict
def subarray_sum(a, k):
    counts = defaultdict(int); counts[0] = 1     # the seed
    running = total = 0
    for v in a:
        running += v
        total += counts[running - k]
        counts[running] += 1
    return total
```
**The bug:** forgetting `counts[0] = 1` — you miss every subarray starting at index 0.

### Set + run-head guard
```python
def longest_consecutive(a):
    s = set(a); best = 0
    for v in s:
        if v - 1 in s: continue          # not a run head — skip
        n = v; length = 1
        while n + 1 in s: n += 1; length += 1
        best = max(best, length)
    return best
```
**That one `continue` is the whole problem.** It makes each run traversed exactly once,
so the nested loop is `O(n)`. Without it the code is still *correct* — it just passes the
samples at `O(n²)` and dies on the large input.

### Canonical key grouping
```python
def group_anagrams(words):
    g = defaultdict(list)
    for w in words:
        key = [0] * 26
        for ch in w: key[ord(ch) - 97] += 1
        g[tuple(key)].append(w)          # count tuple avoids the O(L log L) sort
    return list(g.values())
```

### Frequency, then bucket
```python
from collections import Counter
def top_k_frequent(a, k):
    cnt = Counter(a); buckets = [[] for _ in range(len(a) + 1)]
    for v, c in cnt.items(): buckets[c].append(v)
    out = []
    for c in range(len(a), 0, -1):
        for v in buckets[c]:
            out.append(v)
            if len(out) == k: return out
    return out
```
`O(n)`, beating the heap's `O(n log k)` because frequency is bounded by `n`.
**Name the heap solution first, then beat it.**

---

## 3. Sliding window

**Precondition:** the window needs monotonicity — extending it must move the objective
predictably. **Negatives break this.** Then you switch to prefix sums + hash.

### Fixed size
```python
def max_sum_k(a, k):
    s = sum(a[:k]); best = s
    for i in range(k, len(a)):
        s += a[i] - a[i - k]           # add entrant, subtract leaver — never recompute
        best = max(best, s)
    return best
```

### Variable — longest satisfying
`hi` always advances; `lo` only jumps to restore validity.

```python
def longest_unique(s):
    last = {}; lo = best = 0
    for hi, ch in enumerate(s):
        if ch in last and last[ch] >= lo:     # >= lo is the staleness guard
            lo = last[ch] + 1
        last[ch] = hi
        best = max(best, hi - lo + 1)
    return best
```
**The bug:** without `>= lo`, a stale index from before the current window drags `lo`
backwards.

### Variable — shortest satisfying
```python
def min_subarray_len(target, a):
    lo = 0; s = 0; best = float('inf')
    for hi, v in enumerate(a):
        s += v
        while s >= target:                    # while, NOT if
            best = min(best, hi - lo + 1)
            s -= a[lo]; lo += 1
    return 0 if best == float('inf') else best
```
`while` rather than `if` is the entire problem.

### Frequency window with a counter
```python
def longest_repl(s, k):        # longest run after replacing <= k chars
    cnt = defaultdict(int); lo = best = maxf = 0
    for hi, ch in enumerate(s):
        cnt[ch] += 1; maxf = max(maxf, cnt[ch])
        while (hi - lo + 1) - maxf > k:       # chars needing replacement
            cnt[s[lo]] -= 1; lo += 1
        best = max(best, hi - lo + 1)
    return best

def min_window(s, t):
    if not s or not t: return ""
    need = Counter(t); missing = len(t)
    lo = 0; best = (float('inf'), 0, 0)
    for hi, ch in enumerate(s):
        if need[ch] > 0: missing -= 1         # only counts if still needed
        need[ch] -= 1                         # goes negative for surplus — fine
        while missing == 0:
            if hi - lo + 1 < best[0]: best = (hi - lo + 1, lo, hi)
            need[s[lo]] += 1
            if need[s[lo]] > 0: missing += 1
            lo += 1
    return "" if best[0] == float('inf') else s[best[1]:best[2] + 1]
```
A `missing` counter is cleaner than comparing two dicts each step.

**Say the amortization out loud:** each index enters and leaves at most once, so it's
`O(n)` despite the nested loop.

---

## 4. Binary search

### Boundary form — use this one by default
For anything asking *where* rather than *whether*. Returns the insertion point, never
infinite-loops, no special not-found branch.

```python
def lower_bound(a, target):            # first index with a[i] >= target
    lo, hi = 0, len(a)                 # half-open: hi is one past the end
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < target: lo = mid + 1
        else:               hi = mid
    return lo
```

### Plain search
```python
def bsearch(a, target):
    lo, hi = 0, len(a) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2      # overflow-safe habit (matters in C++/Java)
        if a[mid] == target: return mid
        if a[mid] < target: lo = mid + 1
        else:               hi = mid - 1
    return -1
```

### Rotated sorted array
One half is always sorted — identify which, then check whether the target lies inside it.

```python
def search_rotated(a, t):
    lo, hi = 0, len(a) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] == t: return mid
        if a[lo] <= a[mid]:                        # left half sorted
            if a[lo] <= t < a[mid]: hi = mid - 1
            else:                   lo = mid + 1
        else:                                      # right half sorted
            if a[mid] < t <= a[hi]: lo = mid + 1
            else:                   hi = mid - 1
    return -1

def find_min_rotated(a):
    lo, hi = 0, len(a) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] > a[hi]: lo = mid + 1            # min is right of mid
        else:              hi = mid
    return a[lo]
```
**Caveat to state:** with duplicates this degrades to `O(n)` — `a[lo] == a[mid]` no
longer tells you which half is sorted.

### Binary search on the answer
When the question is "smallest capacity/speed/size that works," you're searching the
answer range for the boundary of a monotone predicate, not searching an array.

```python
def min_feasible(lo, hi, feasible):    # smallest x in [lo, hi] with feasible(x) True
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid): hi = mid
        else:             lo = mid + 1
    return lo

def ship_days(weights, days):          # example: min capacity to ship within `days`
    def ok(cap):
        d, cur = 1, 0
        for w in weights:
            if cur + w > cap: d += 1; cur = 0
            cur += w
        return d <= days
    return min_feasible(max(weights), sum(weights), ok)
```
The whole job is writing `feasible(x)` and **stating why it's monotone** (if capacity `x`
works, `x+1` works). `O(n log(range))`.

---

## 5. Sorting

Usually the sort is the *setup*, not the problem: sort, then one linear pass.

```python
def merge_intervals(iv):
    iv.sort(key=lambda x: x[0])
    out = []
    for s, e in iv:
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)   # max, not e — nested-interval case
        else:
            out.append([s, e])
    return out
```
`max(out[-1][1], e)` rather than `= e` is the correctness question: one interval can be
fully contained in another.

```python
def insert_interval(iv, new):
    out = []; i = 0; n = len(iv); s, e = new
    while i < n and iv[i][1] < s: out.append(iv[i]); i += 1     # strictly before
    while i < n and iv[i][0] <= e:                               # overlapping
        s = min(s, iv[i][0]); e = max(e, iv[i][1]); i += 1
    out.append([s, e])
    while i < n: out.append(iv[i]); i += 1                       # strictly after
    return out

def min_rooms(iv):                     # two-array sweep
    starts = sorted(x[0] for x in iv)
    ends   = sorted(x[1] for x in iv)
    best = cur = 0; j = 0
    for s in starts:
        while j < len(ends) and ends[j] <= s: cur -= 1; j += 1
        cur += 1; best = max(best, cur)
    return best
```
Sorting starts and ends *independently* is the trick — you never need to know which end
belongs to which start, only how many rooms are open at each start.

### The multi-key sort idiom
Descending numeric with an ascending string tiebreak, in one key. Most useful single line
here, and the one people fumble under pressure.

```python
sorted(rows, key=lambda r: (-r["count"], r["name"]))
```

### Sort properties — asked conversationally
| | Average | Worst | Space | Stable |
|---|---|---|---|---|
| Quicksort | `n log n` | **`n²`** (sorted input, bad pivot) | `log n` | No |
| Mergesort | `n log n` | `n log n` | **`n`** | Yes |
| Heapsort | `n log n` | `n log n` | `1` | No |
| Python `sorted` (Timsort) | `n log n` | `n log n` | `n` | **Yes**, adaptive on runs |

**"Can you beat `O(n log n)`?"** Only by not comparing — counting or radix sort when the
key range is bounded.

---

## 6. Prefix sums, Kadane, difference arrays

```python
def max_subarray(a):                   # Kadane
    best = cur = a[0]
    for v in a[1:]:
        cur = max(v, cur + v)          # extend, or restart here
        best = max(best, cur)
    return best
```
**The bug:** initialising `best = 0` breaks the all-negative case. Seed from `a[0]`.

```python
def max_profit(p):                     # buy low, sell later — one pass
    lo = float('inf'); best = 0
    for v in p:
        lo = min(lo, v); best = max(best, v - lo)
    return best

def product_except_self(a):            # no division, O(n), O(1) extra
    n = len(a); res = [1] * n
    pre = 1
    for i in range(n): res[i] = pre; pre *= a[i]        # prefix pass
    suf = 1
    for i in range(n - 1, -1, -1): res[i] *= suf; suf *= a[i]   # suffix pass
    return res

def range_add(n, updates):             # difference array: O(1) range updates
    d = [0] * (n + 1)
    for l, r, v in updates:
        d[l] += v; d[r + 1] -= v       # mark start and one-past-end
    out = []; run = 0
    for i in range(n): run += d[i]; out.append(run)     # prefix sum to materialize
    return out
```
Difference array is the inverse of prefix sum: `O(1)` per range update, one `O(n)` pass at
the end to read the array back.

---

## 7. Linked lists

**Two habits that prevent nearly every bug:** save `next` *before* rewiring, and use a
**dummy head** so empty-list and delete-the-head stop being special cases.

```python
class Node:
    def __init__(self, val, nxt=None): self.val = val; self.next = nxt

def reverse(head):
    prev = None
    while head:
        nxt = head.next          # save BEFORE rewiring or the rest is lost
        head.next = prev
        prev = head
        head = nxt
    return prev

def has_cycle(head):             # Floyd — fast laps slow inside any cycle
    slow = fast = head
    while fast and fast.next:
        slow = slow.next; fast = fast.next.next
        if slow is fast: return True
    return False

def middle(head):                # same two-speed trick, different stop rule
    slow = fast = head
    while fast and fast.next:
        slow = slow.next; fast = fast.next.next
    return slow

def merge_sorted(a, b):
    dummy = Node(0); tail = dummy
    while a and b:
        if a.val <= b.val: tail.next = a; a = a.next
        else:              tail.next = b; b = b.next
        tail = tail.next
    tail.next = a or b           # whichever still has nodes
    return dummy.next

def remove_nth_from_end(head, n):
    dummy = Node(0, head); fast = slow = dummy
    for _ in range(n): fast = fast.next      # open a gap of n
    while fast.next:
        fast = fast.next; slow = slow.next
    slow.next = slow.next.next
    return dummy.next
```

### In C++ — the pointer-to-pointer idiom
Replaces the dummy head, allocates nothing, and removes the head special case. This is
what reads as someone who has actually written C++.

```cpp
bool remove(int target) {
    Node** pp = &head;
    while (*pp && (*pp)->val != target) pp = &(*pp)->next;
    if (!*pp) return false;
    Node* dead = *pp;
    *pp = dead->next;          // identical whether or not this was the head
    delete dead;
    return true;
}
```

If you own raw pointers, you owe the **Rule of Three**: destructor, copy constructor,
copy assignment. And **the destructor must iterate, not recurse** — recursive destruction
stack-overflows on a long list.

```cpp
~List() { Node* c = head; while (c) { Node* nx = c->next; delete c; c = nx; } }
```

---

## 8. Matrix and strings

```python
def spiral_order(m):
    if not m or not m[0]: return []
    res = []; top, bot, left, right = 0, len(m) - 1, 0, len(m[0]) - 1
    while top <= bot and left <= right:
        for c in range(left, right + 1): res.append(m[top][c])
        top += 1
        for r in range(top, bot + 1): res.append(m[r][right])
        right -= 1
        if top <= bot:                                     # guard: single row left
            for c in range(right, left - 1, -1): res.append(m[bot][c])
            bot -= 1
        if left <= right:                                  # guard: single col left
            for r in range(bot, top - 1, -1): res.append(m[r][left])
            left += 1
    return res
```
**The bug:** the two inner guards. Without them a single remaining row or column gets
emitted twice.

```python
def rotate90(m):                       # in place, clockwise
    n = len(m)
    for r in range(n):
        for c in range(r + 1, n):      # transpose (c starts at r+1, not 0)
            m[r][c], m[c][r] = m[c][r], m[r][c]
    for row in m: row.reverse()        # then mirror each row
    return m
```
**The bug:** `range(r + 1, n)`. Starting at `0` swaps everything twice and gives you the
original matrix back.

```python
def is_palindrome(s):                  # ignoring non-alphanumerics
    lo, hi = 0, len(s) - 1
    while lo < hi:
        while lo < hi and not s[lo].isalnum(): lo += 1
        while lo < hi and not s[hi].isalnum(): hi -= 1
        if s[lo].lower() != s[hi].lower(): return False
        lo += 1; hi -= 1
    return True
```
Skip loops must re-check `lo < hi` or you run off the end on degenerate input.

```python
def longest_pal_substr(s):             # expand around center — O(n^2), O(1)
    if not s: return ""
    best = (0, 0)
    def expand(l, r):
        while l >= 0 and r < len(s) and s[l] == s[r]: l -= 1; r += 1
        return l + 1, r - 1            # step back inside the last valid pair
    for i in range(len(s)):
        for l, r in (expand(i, i), expand(i, i + 1)):   # odd and even centers
            if r - l > best[1] - best[0]: best = (l, r)
    return s[best[0]:best[1] + 1]
```
**Both center types matter** — `2n-1` centers, not `n`. Missing the even case fails
`"cbbd"`.

```python
def rotate_array(a, k):                # rotate right by k, in place
    n = len(a); k %= n                 # k can exceed n
    a.reverse(); a[:k] = reversed(a[:k]); a[k:] = reversed(a[k:])
    return a
```

---

## 9. Stack

```python
def valid_parens(s):
    pairs = {')': '(', ']': '[', '}': '{'}; st = []
    for ch in s:
        if ch in "([{": st.append(ch)
        elif ch in pairs:
            if not st or st.pop() != pairs[ch]: return False
    return not st                      # leftovers = unclosed
```

```python
def daily_temperatures(T):             # monotonic stack: next greater element
    res = [0] * len(T); st = []        # stack holds indices still awaiting an answer
    for i, t in enumerate(T):
        while st and T[st[-1]] < t:
            j = st.pop(); res[j] = i - j
        st.append(i)
    return res
```
Each index is pushed and popped at most once → `O(n)` despite the inner `while`.

---

## Complexity quick reference

| Operation | Cost |
|---|---|
| dict / set lookup, insert | `O(1)` average |
| `list.append` / `pop()` | `O(1)` amortized |
| `list.pop(0)` / `insert(0, x)` | **`O(n)`** — use `collections.deque` |
| `x in list` | **`O(n)`** — use a set |
| slicing `a[i:j]` | `O(j - i)` — copies |
| `sorted()` / `.sort()` | `O(n log n)` |
| string concat in a loop | **`O(n²)`** — build a list, `"".join()` |

---

## Python idioms worth having ready

```python
from collections import defaultdict, Counter, deque

defaultdict(list); defaultdict(int)           # grouping, counting
Counter(xs).most_common(k)
d.get(key, default)
sorted(xs, key=lambda r: (-r.count, r.name))  # desc numeric, asc string tiebreak
enumerate(xs, start=1)
zip(*rows)                                    # transpose
any(...) / all(...)
s.split(sep, maxsplit)
float('inf') / float('-inf')                  # sentinels
a[::-1]                                       # reverse copy
divmod(n, k)
deque()                                       # O(1) popleft
```
**Gotcha:** `itertools.groupby` groups *consecutive runs* — the input must already be
sorted by the same key.

---

## The protocol

1. **Restate the problem, confirm edge cases** — empty, one element, duplicates,
   negatives. Thirty seconds, and it routes you to the right family.
2. **Ask "are all the values positive?"** on any subarray problem.
3. **State the family, the approach, and both complexities — before typing.**
4. **Say the invariant out loud while writing the loop.** That's the difference between
   reciting a template and understanding one, and it's what's being listened for.
5. **Trace one small case at the end**, including an edge case, without being asked.

**Read constraints for what they rule out.** An `O(1)` space requirement exists
specifically to eliminate the hash-map solution — saying so proves you read the
constraints instead of pattern-matching.

**If you're stuck:** say what you'd do brute-force and its complexity, then ask what's
redundant about it. Every technique here is a specific answer to "what work am I
repeating?" — sorting removes the need to compare all pairs, hashing removes the rescan,
two pointers removes the inner loop, prefix sums remove the recomputation.
