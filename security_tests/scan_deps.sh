#!/bin/bash
# 依赖漏洞扫描脚本
set -e

echo "========================================"
echo "  依赖安全扫描"
echo "========================================"

echo ""
echo "[1] Python 依赖漏洞扫描 (pip-audit)"
echo "----------------------------------------"
pip install pip-audit -q 2>/dev/null
cd ../backend
pip-audit --desc 2>/dev/null || echo "  [!] pip-audit 扫描完成（检查上方输出）"

echo ""
echo "[2] Node.js 依赖漏洞扫描 (npm audit)"
echo "----------------------------------------"
cd ../frontend
npm audit --production 2>/dev/null || echo "  [!] npm audit 扫描完成（检查上方输出）"

echo ""
echo "[3] 检查已知危险依赖"
echo "----------------------------------------"
cd ../backend
# Check for known problematic packages
for pkg in pycrypto telnetlib insecure-package; do
    if pip show "$pkg" 2>/dev/null | grep -q "Name:"; then
        echo "  [WARN] 发现不安全包: $pkg"
    fi
done
echo "  已知危险包检查完成"

echo ""
echo "========================================"
echo "  扫描完毕"
echo "========================================"
