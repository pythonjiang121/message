#!/bin/bash

# 显示帮助信息
show_help() {
  echo "短信审核系统Docker部署脚本"
  echo "用法: $0 [选项]"
  echo "选项:"
  echo "  -b, --build    重新构建Docker镜像"
  echo "  -r, --restart  重启服务"
  echo "  -s, --stop     停止服务"
  echo "  -l, --logs     查看日志"
  echo "  -a, --api      运行API服务模式"
  echo "  -c, --check    运行检查模式"
  echo "  -h, --help     显示此帮助信息"
}

# 创建备份
create_backup() {
  timestamp=$(date +%Y%m%d_%H%M%S)
  backup_dir="backup_$timestamp"
  mkdir -p $backup_dir
  cp *.py $backup_dir/
  echo "已创建代码备份到 $backup_dir/"
}

# 处理命令行参数
case "$1" in
  -b|--build)
    create_backup
    echo "构建并启动Docker服务..."
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    echo "服务已启动，查看日志请执行 '$0 --logs'"
    ;;
  
  -r|--restart)
    echo "重启Docker服务..."
    docker compose restart
    ;;
  
  -s|--stop)
    echo "停止Docker服务..."
    docker compose down
    ;;
  
  -l|--logs)
    if [ "$2" = "api" ]; then
      echo "显示API服务日志..."
      docker compose logs -f sms-audit-api
    elif [ "$2" = "check" ]; then
      echo "显示检查服务日志..."
      docker compose logs -f sms-audit-check
    else
      echo "显示处理服务日志..."
      docker compose logs -f sms-audit
    fi
    ;;
  
  -a|--api)
    echo "启动API服务模式..."
    create_backup
    docker compose --profile api up -d
    echo "API服务已启动，查看日志请执行 '$0 --logs api'"
    ;;
  
  -c|--check)
    echo "运行检查模式..."
    create_backup
    docker compose --profile check up
    ;;
  
  -h|--help)
    show_help
    ;;
  
  *)
    if [ -z "$1" ]; then
      echo "启动标准处理服务..."
      docker compose up -d
      echo "服务已启动，查看日志请执行 '$0 --logs'"
    else
      echo "未知选项: $1"
      show_help
      exit 1
    fi
    ;;
esac 