# frontend

`frontend/` 是 `gaokao-pilot` 的前端骨架，基于 React + TypeScript + Vite，已经预置：

- TailwindCSS
- React Router
- Axios 请求实例
- 一个可访问后端健康检查接口的示例页

## 启动方式

1. 进入前端目录：

```powershell
cd frontend
```

2. 安装依赖：

```powershell
npm install
```

3. 启动开发服务器：

```powershell
npm run dev
```

默认访问地址：

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`

## 后端联调

开发环境下，Vite 已代理以下路径到本地 FastAPI：

- `/api`
- `/qa`
- `/schools`
- `/recommendations`
- `/reports`

因此默认不需要额外配置就可以请求后端。

如果你希望前端直连其他后端地址，可以新建 `.env`：

```powershell
Copy-Item .env.example .env
```

然后设置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 当前骨架包含

- 首页 `/`
- 健康检查页 `/health`
- 404 页面

后续可以继续在 `src/pages/` 中补充学校检索、成绩分析、推荐结果和问答页面。
