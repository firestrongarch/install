#include <QApplication>
#include <QMainWindow>
#include "PackageInfoWidget.h"

int main(int argc, char *argv[]){
    QApplication app(argc, argv);
    // QMainWindow window;
    // qDebug() << "win is hidden: "<< window.isHidden();
    // window.show();

    PackageInfoWidget widget;
    widget.show();

    return app.exec();
}