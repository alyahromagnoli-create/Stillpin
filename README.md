# Stillpin

截图与参考图悬浮贴图板。Windows 单 EXE 便携版，Tkinter + Pillow + PyMuPDF，会话使用 JSON。

**[下载最新版 Windows EXE](https://github.com/alyahromagnoli-create/Stillpin/releases/latest)** · [详细使用说明](docs/USER_GUIDE.zh-CN.md)

当前版本：**1.1.0**。无需安装 Python 或开发库，不要求电脑存在 D 盘。

## 功能

- 区域截图、剪贴板图片、文件拖入与独立置顶贴图窗。
- 图片缩放/平移、透明度、PDF 翻页与文本预览。
- 导入素材保存副本，会话采用相对路径，随 data 一起移动。
- 新版为单 EXE，运行无需旧版 _internal 文件夹。

## 使用与数据

下载 Release 中的 `Stillpin.exe`，放在可写文件夹后双击。首次解包需要几秒，解包使用 Windows 系统临时目录，程序退出后由运行时清理。

全新使用只需 EXE。保留已有记录时，先退出旧版，再把 EXE 和旁边的 **data** 文件夹一起移动或备份。持续修改的数据独立存储，不能永久写回 EXE。本仓库和下载包不包含真实个人记录。

Word、PPT 等材料请截图后粘贴，不做原生 Office 渲染；GIF 为首帧，加密 PDF 不支持。

## 验证范围

6 项项目测试通过；独立 EXE 在清理 Python 环境变量、限制 PATH、中文空格路径和不同工作目录下运行，并验证程序连同 data 复制到新位置后的重启与记录恢复。发布 EXE 与对应 Python 核心源码已核对。

目前仅在本机 Windows 11 x64 验证；尚未在第二台实体电脑、Windows 10 或其他架构实机验证。程序未签名。

## 从源码构建

Windows x64 + Python 3.12：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\build-portable.ps1
```

构建缓存和中间文件放在项目内的 work，输出路径见构建脚本。EXE 仅作为 Release 附件发布。

## 许可

原始应用与图标：**AGPL-3.0**，见 [LICENSE](LICENSE)。第三方组件保留各自许可，相关原文随源码或便携包附带。
