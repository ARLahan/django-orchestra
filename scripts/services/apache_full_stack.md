Apache 2 MPM Event with PHP-FPM, FCGID and SUEXEC on Debian Jessie
==================================================================

The goal of this setup is having a high-performance state-of-the-art deployment of Apache and PHP while being compatible with legacy applications.

* Apache Event MPM engine handles requests asynchronously, instead of using a dedicated thread or process per request.

* PHP-FPM is a FastCGI process manager included in modern versions of PHP.
    Compared to FCGID it provides better process management features and enables the OPCache to be shared between workers.

* FCGID and SuEXEC are used for legacy apps that need older versions of PHP (i.e. PHP 5.2 or PHP 4)


*Sources:*
  * Source http://wiki.apache.org/httpd/PHP-FPM


*Related:*
  * [PHP4 on debian](php4_on_debian.md)
  * [VsFTPd](vsftpd.md)
  * [Webalizer](webalizer.md)



1. Install the machinery
    ```bash
    apt-get update
    apt-get install apache2-mpm-event php5-fpm libapache2-mod-fcgid apache2-suexec-custom php5-cgi
    ```


2. Enable some convinient Apache modules
    ```bash
    a2enmod suexec
    a2enmod ssl
    a2enmod auth_pam
    a2enmod proxy_fcgi
    a2emmod userdir
    ```
    * TODO compat module
    https://httpd.apache.org/docs/trunk/mod/mod_access_compat.html


3. Configure `suexec-custom`
    ```bash
    sed -i "s#/var/www#/home#" /etc/apache2/suexec/www-data
    sed -i "s#public_html#webapps#" /etc/apache2/suexec/www-data
    ```


4. Create logs directory for virtualhosts
    ```bash
    mkdir -p /var/log/apache2/virtual/
    chown -R www-data:www-data /var/log/apache2
    ```


5. Restart Apache
    ```bash
    service apache2 restart
    ```


* TODO 
    libapache2-mod-auth-pam
    https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=710770


* ExecCGI
    ```bash
    <Directory /home/*/webapps/>
        Options +ExecCGI
    </Directory>
    ```


TODO CHRoot
    https://andrewbevitt.com/tutorials/apache-varnish-chrooted-php-fpm-wordpress-virtual-host/

    ```bash
    echo '
    [vhost]
    istemplate = 1
    listen.mode = 0660
    pm.max_children = 5
    pm.start_servers = 1
    pm.min_spare_servers = 1
    pm.max_spare_servers = 2
    ' > /etc/php5/fpm/conf.d/vhost-template.conf
    ```

    ```bash
    mkdir -p /var/run/fpm/socks/
    chmod 771 /var/run/fpm/socks
    chown orchestra.orchestra /var/run/fpm/socks
    ```
