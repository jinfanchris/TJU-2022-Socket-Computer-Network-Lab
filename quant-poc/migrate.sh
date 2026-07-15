#!/usr/bin/env bash
#
# migrate.sh — 把本项目的 quant-poc/ 子目录迁移成一个独立仓库。
#
# 做的事:
#   * 全新克隆一份源分支(不动你现有的任何仓库/工作区)
#   * 把 quant-poc/ 提为仓库根目录,只保留触及它的提交(丢掉无关的旧历史与文件)
#   * 推送到你事先建好的【空的私有仓库】
#
# 用前提:先在 GitHub 上手动建一个【空仓库】quant-trading-poc
#         (Private,不要勾 README / .gitignore / license)。
#
# 用法:
#   bash migrate.sh                 # 交互确认后推送
#   AUTO_YES=1 bash migrate.sh      # 跳过确认,直接推送(真·一键)
#
# 常用覆盖项(环境变量):
#   NEW_REPO_URL=git@github.com:jinfanchris/quant-trading-poc.git bash migrate.sh
#
set -euo pipefail

# ---- 可配置项(可用环境变量覆盖) ----
SRC_REPO_URL="${SRC_REPO_URL:-https://github.com/jinfanchris/TJU-2022-Socket-Computer-Network-Lab.git}"
SRC_BRANCH="${SRC_BRANCH:-claude/quant-trading-poc-wqhsfb}"
SUBDIR="${SUBDIR:-quant-poc}"
NEW_REPO_URL="${NEW_REPO_URL:-https://github.com/jinfanchris/quant-trading-poc.git}"
TARGET_BRANCH="${TARGET_BRANCH:-main}"
WORKDIR="${WORKDIR:-quant-trading-poc}"
AUTO_YES="${AUTO_YES:-0}"

echo "== 迁移配置 =="
echo "  源仓库  : $SRC_REPO_URL"
echo "  源分支  : $SRC_BRANCH"
echo "  子目录  : $SUBDIR/  ->  新仓库根目录"
echo "  新仓库  : $NEW_REPO_URL  (分支 $TARGET_BRANCH)"
echo "  工作目录: ./$WORKDIR"
echo

command -v git >/dev/null 2>&1 || { echo "!! 需要 git,请先安装。" >&2; exit 1; }

if [ -e "$WORKDIR" ]; then
  echo "!! 目录 '$WORKDIR' 已存在。请删除它,或用 WORKDIR=别的名字 重跑。" >&2
  exit 1
fi

echo "[1/5] 克隆源分支到临时工作目录(不影响你现有的仓库)..."
git clone --branch "$SRC_BRANCH" --single-branch "$SRC_REPO_URL" "$WORKDIR"
cd "$WORKDIR"

if [ ! -d "$SUBDIR" ]; then
  echo "!! 源分支里找不到 '$SUBDIR/' 目录,已终止。" >&2
  exit 1
fi

echo "[2/5] 把 $SUBDIR/ 提为仓库根,只保留触及它的提交..."
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f --subdirectory-filter "$SUBDIR" "$SRC_BRANCH"

echo "[3/5] 清理 filter-branch 的备份引用..."
git for-each-ref --format='%(refname)' refs/original/ | while read -r ref; do
  git update-ref -d "$ref"
done
git reflog expire --expire=now --all >/dev/null 2>&1 || true
git gc --prune=now --quiet >/dev/null 2>&1 || true

echo "[4/5] 重命名分支为 $TARGET_BRANCH,指向新仓库..."
git branch -M "$TARGET_BRANCH"
git remote set-url origin "$NEW_REPO_URL"

echo
echo "将把下列提交推送到  $NEW_REPO_URL  ($TARGET_BRANCH):"
git --no-pager log --oneline
echo
echo "推送后,新仓库根目录将包含:"
git --no-pager ls-tree --name-only HEAD | sed 's/^/    /'
echo

if [ "$AUTO_YES" != "1" ]; then
  printf "确认推送? [y/N] "
  read -r ans
  case "$ans" in
    [yY]) ;;
    *) echo "已取消推送。干净的代码已准备在 ./$WORKDIR,你可以手动 'git push -u origin $TARGET_BRANCH'。"; exit 0 ;;
  esac
fi

echo "[5/5] 推送到新仓库..."
git push -u origin "$TARGET_BRANCH"

echo
echo "✅ 完成!"
echo "   新仓库  : $NEW_REPO_URL"
echo "   本地副本: ./$WORKDIR   <- 在这个目录里开新 session 即可"
echo "   下一步  : cd $WORKDIR && make install && make backend"
