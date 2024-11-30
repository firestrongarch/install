#include <QApplication>
#include <QMainWindow>
#include <qcontainerfwd.h>
#include "PackageInfoWidget.h"
#include "SelectionWidget.h"

class MainWindow : public QMainWindow {
public:
    MainWindow(QWidget *parent = nullptr) : QMainWindow(parent) {
        QWidget *centralWidget = new QWidget(this);
        QHBoxLayout *layout = new QHBoxLayout(centralWidget);

        // 创建四个 SelectionWidget 实例
        for (auto &widget : selectionWidgets) {
            widget = new SelectionWidget(); // 初始化每个元素
        }

        const QStringList slamType = {"ORB_SLAM2", "ov2slam", "VINS_MONO", "ssvio","null"};
        const QStringList datasetsType = {"kitti", "euroc", "uma", "null"};
        const QStringList sensorsType = {"mono", "stereo", "null"};
        const QStringList loopType = {"ON", "OFF", "null"};

        selectionWidgets[0]->setOptions(slamType);
        selectionWidgets[1]->setOptions(datasetsType);
        selectionWidgets[2]->setOptions(sensorsType);
        selectionWidgets[3]->setOptions(loopType);

        // 将四个组件添加到布局中
        for (auto& widget : selectionWidgets) {
            layout->addWidget(widget);
        }

        QPushButton *button = new QPushButton("run", this);
        layout->addWidget(button);
        connect(button, &QPushButton::clicked, this, &MainWindow::runCommand);

        // 设置中心部件及其布局
        this->setCentralWidget(centralWidget);

        // 显示主窗口
        this->show();
    }
private:
    QVector<SelectionWidget*> selectionWidgets{4};
    QProcess *process;

    void runCommand(){
        qDebug() << "run!";
        process = new QProcess(this);

        // 示例命令：安装一个包
        QString command = "stereo_kitti /data/datasets/vocabulary/ORBvoc.txt /data/datasets/config/ORB_SLAM2/KITTI00-02.yaml  /data/datasets/kitti/sequences/00";
        qDebug() << "Starting command:" << command;
        process->start("zsh",QStringList() << "-c" << command);

        if (!process->waitForStarted()) {
            qDebug() << "Failed to start process";
        } else {
            qDebug() << "Process started successfully";
        }
    }
};

int main(int argc, char *argv[]){
    QApplication app(argc, argv);
    // QMainWindow window;
    // qDebug() << "win is hidden: "<< window.isHidden();
    // window.show();

    MainWindow window;

    return app.exec();
}