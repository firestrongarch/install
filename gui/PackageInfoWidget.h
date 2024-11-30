#pragma once
#include <QTextEdit>
#include <QFile>
#include <QTextStream>
#include <QVBoxLayout>
#include <QWidget>
#include <QLabel>
#include <QMap>
#include <QMessageBox>
#include <qdebug.h>
#include <qlogging.h>
#include <yaml-cpp/yaml.h>
#include <QInputDialog>
#include <QPushButton>
#include <QDebug>
#include <QProcess>

class PackageInfoWidget : public QWidget {
public:
    PackageInfoWidget(QWidget *parent = nullptr) : QWidget(parent) {
        QVBoxLayout *layout = new QVBoxLayout(this);

        QLabel *title = new QLabel("Package Information", this);
        layout->addWidget(title);

        textEdit = new QTextEdit(this);
        textEdit->setReadOnly(true);
        layout->addWidget(textEdit);

        QPushButton *button = new QPushButton("Select Package", this);
        layout->addWidget(button);
        connect(button, &QPushButton::clicked, this, &PackageInfoWidget::showPackageSelection);

        QPushButton *buttonRun = new QPushButton("install", this);
        layout->addWidget(buttonRun);
        connect(buttonRun, &QPushButton::clicked, this, &PackageInfoWidget::runCommand);
        

        if (loadPackageInfo()) {
            updatePackageInfo("");
        } else {
            textEdit->setText("Failed to load package information.");
        }
    }

private:
    QTextEdit *textEdit;
    QString packageInfoText;
    QList<QString> packageNames;
    QMap<QString, QString> packageDetails;
    QProcess *process;

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
                QString name = QString::fromStdString(pkg["name"].as<std::string>());
                QString description = QString::fromStdString(pkg["des"].as<std::string>());
                QString url = QString::fromStdString(pkg["url"].as<std::string>());
                QString version = QString::fromStdString(pkg["version"].as<std::string>());

                packageDetails[name] = QString("Name: %1\nDescription: %2\nURL: %3\nVersion: %4\n")
                                      .arg(name)
                                      .arg(description)
                                      .arg(url)
                                      .arg(version);

                packageNames.append(name);
            }
        } catch (const YAML::Exception &e) {
            QMessageBox::critical(this, "Error", QString::fromStdString(e.what()));
            return false;
        }

        return true;
    }

    void showPackageSelection() {
        bool ok;
        QString selectedPackage = QInputDialog::getItem(this, "Select Package", "Choose a package:", packageNames, 0, false, &ok);

        if (ok && !selectedPackage.isEmpty()) {
            QPushButton *button = qobject_cast<QPushButton*>(sender());
            button->setText(selectedPackage);
            updatePackageInfo(selectedPackage);
        }
    }

    void updatePackageInfo(const QString &packageName) {
        if (packageDetails.contains(packageName)) {
            textEdit->setText(packageDetails[packageName]);
        } else {
            textEdit->setText("No package selected or package details not found.");
        }
    }

    void runCommand() {
        qDebug() << "runCommand called";

        process = new QProcess(this);
        connect(process, &QProcess::readyReadStandardOutput, this, &PackageInfoWidget::onReadyReadStandardOutput);
        connect(process, &QProcess::readyReadStandardError, this, &PackageInfoWidget::onReadyReadStandardError);
        connect(process, QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished), this, &PackageInfoWidget::onFinished);

        // 示例命令：安装一个包
        QString command = "sudo apt-get dist-upgrade";
        qDebug() << "Starting command:" << command;
        process->start("zsh",QStringList() << "-c" << command);

        if (!process->waitForStarted()) {
            qDebug() << "Failed to start process";
        } else {
            qDebug() << "Process started successfully";
        }
    }

    void onReadyReadStandardOutput() {
        QByteArray output = process->readAllStandardOutput();
        textEdit->append(QString::fromUtf8(output));  // 将输出显示在 QTextEdit 中
        qDebug() << "Standard Output:" << output;
    }

    void onReadyReadStandardError() {
        QByteArray error = process->readAllStandardError();
        textEdit->append(QString::fromUtf8(error));  // 将错误显示在 QTextEdit 中
        qDebug() << "Standard Error:" << error;
    }

    void onFinished(int exitCode, QProcess::ExitStatus exitStatus) {
        textEdit->append(QString("Process finished with exit code %1 and status %2").arg(exitCode).arg(static_cast<int>(exitStatus)));  // 将完成信息显示在 QTextEdit 中
        qDebug() << "Process finished with exit code" << exitCode << "and status" << exitStatus;
    }
};