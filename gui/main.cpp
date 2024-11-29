#include <QApplication>
#include <QMainWindow>
#include <QTextEdit>
#include <QFile>
#include <QTextStream>
#include <QVBoxLayout>
#include <QWidget>
#include <QLabel>
#include <QMap>
#include <QMessageBox>
#include <qdebug.h>
#include <yaml-cpp/yaml.h>

class PackageInfoWidget : public QWidget {
public:
    PackageInfoWidget(QWidget *parent = nullptr) : QWidget(parent) {
        QVBoxLayout *layout = new QVBoxLayout(this);

        QLabel *title = new QLabel("Package Information", this);
        layout->addWidget(title);

        QTextEdit *textEdit = new QTextEdit(this);
        textEdit->setReadOnly(true);
        layout->addWidget(textEdit);

        if (loadPackageInfo()) {
            textEdit->setText(packageInfoText);
        } else {
            textEdit->setText("Failed to load package information.");
        }
    }

private:
    QString packageInfoText;

    bool loadPackageInfo() {
        QFile file("../../packages.yaml");
        if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
            QMessageBox::critical(this, "Error", "Could not open file for reading.");
            return false;
        }

        QTextStream in(&file);
        QString content = in.readAll();
        file.close();

        try {
            YAML::Node doc = YAML::Load(content.toStdString());

            for (const auto &node : doc) {
                const YAML::Node &pkg = node.second;
                packageInfoText += QString("Name: %1\n").arg(QString::fromStdString(pkg["name"].as<std::string>()));
                packageInfoText += QString("Description: %1\n").arg(QString::fromStdString(pkg["des"].as<std::string>()));
                packageInfoText += QString("URL: %1\n").arg(QString::fromStdString(pkg["url"].as<std::string>()));
                packageInfoText += QString("Version: %1\n\n").arg(QString::fromStdString(pkg["version"].as<std::string>()));
            }
        } catch (const YAML::Exception &e) {
            QMessageBox::critical(this, "Error", QString::fromStdString(e.what()));
            return false;
        }

        return true;
    }
};

int main(int argc, char *argv[]){
    QApplication app(argc, argv);
    // QMainWindow window;
    // qDebug() << "win is hidden: "<< window.isHidden();
    // window.show();

    PackageInfoWidget widget;
    widget.show();

    return app.exec();
}