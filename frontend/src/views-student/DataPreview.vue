<template>
  <div class="page-container">
    <div class="page-header">
      <span class="student-badge">{{ store.name }} 同学</span>
    </div>
    <div class="content-card">
      <h2>请先阅读下面两组统计数据</h2>

      <div class="table-section">
        <h3>统计表一：6名同学一分钟仰卧起坐个数统计表</h3>
        <table class="data-table">
          <thead>
            <tr><th>姓名</th><th>周子昂</th><th>许明哲</th><th>沈嘉诚</th><th>叶思涵</th><th>李欣怡</th><th>吴俊杰</th></tr>
          </thead>
          <tbody>
            <tr><td>个数/个</td><td>35</td><td>42</td><td>38</td><td>40</td><td>36</td><td>33</td></tr>
          </tbody>
        </table>
      </div>

      <div class="table-section">
        <h3>统计表二：许明哲连续6天一分钟仰卧起坐成绩统计表</h3>
        <table class="data-table">
          <thead>
            <tr><th>日期</th><th>周一</th><th>周二</th><th>周三</th><th>周四</th><th>周五</th><th>周六</th></tr>
          </thead>
          <tbody>
            <tr><td>个数/个</td><td>30</td><td>32</td><td>35</td><td>36</td><td>39</td><td>42</td></tr>
          </tbody>
        </table>
      </div>

      <p class="hint">阅读完成后，点击下方按钮开始答题。</p>
      <button @click="$router.push('/questions')" class="btn-primary">开始答题</button>
    </div>
  </div>
</template>

<script setup>
import { useStudentStore } from '../stores/student.js'
const store = useStudentStore()
</script>
