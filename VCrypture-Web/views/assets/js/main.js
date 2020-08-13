!(function ($) {
  "use strict";

  /*********************** */
  $(document).ready(() => {
    $('.animation').css('visibility', 'visible');
    $('.animation').css('opacity', 1);

    if ($('.error').html() == "" || $('.error').html == "&#8203;") $('.error').css('display', 'none');
    else $('.error').css('display', 'inline-block');
    if ($('.response').html() == "" || $('.response').html == "&#8203;") $('.response').css('display', 'none');
    else $('.response').css('display', 'inline-block');

    history.replaceState({}, document.title, window.location.href.split('#')[0]);
  });

  $('#service-naorshamir').on('click', () => {
    window.location.href = '/naorshamir';
  });
  $('#service-taghaddoslatif').on('click', () => {
    window.location.href = '/taghaddoslatif';
  });
  $('#service-dhimankasana').on('click', () => {
    window.location.href = '/dhimankasana';
  });

  $('#secret').change((e) => {
    $('label[for="secret"]').text(e.target.value.replace(/^.*[\\\/]/, ''));
  });
  $('#secret1').change((e) => {
    $('label[for="secret1"]').text(e.target.value.replace(/^.*[\\\/]/, ''));
  });
  $('#share1').change((e) => {
    $('label[for="share1"]').text(e.target.value.replace(/^.*[\\\/]/, ''));
  })
  $('#share2').change((e) => {
    $('label[for="share2"]').text(e.target.value.replace(/^.*[\\\/]/, ''));
  })
  $('#share3').change((e) => {
    $('label[for="share3"]').text(e.target.value.replace(/^.*[\\\/]/, ''));
  })
  $('#secret2').change((e) => {
    $('label[for="secret2"]').text(e.target.value.replace(/^.*[\\\/]/, ''));
  });
  $('#share4').change((e) => {
    $('label[for="share4"]').text(e.target.value.replace(/^.*[\\\/]/, ''));
  })
  $('#share5').change((e) => {
    $('label[for="share5"]').text(e.target.value.replace(/^.*[\\\/]/, ''));
  })

  /*********************** */

  // Nav Menu
  $(document).on('click', '.nav-menu a, .mobile-nav a', function (e) {
    if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
      var hash = this.hash;
      var target = $(hash);
      if (target.length) {
        e.preventDefault();

        if ($(this).parents('.nav-menu, .mobile-nav').length) {
          $('.nav-menu .active, .mobile-nav .active').removeClass('active');
          $(this).closest('li').addClass('active');
        }

        if (hash == '#header') {
          $('#header').removeClass('header-top');
          $("section").removeClass('section-show');
          return;
        }

        if (!$('#header').hasClass('header-top')) {
          $('#header').addClass('header-top');
          setTimeout(function () {
            $("section").removeClass('section-show');
            $(hash).addClass('section-show');

          }, 350);
        } else {
          $("section").removeClass('section-show');
          $(hash).addClass('section-show');
        }

        $('html, body').animate({
          scrollTop: 0
        }, 350);

        if ($('body').hasClass('mobile-nav-active')) {
          $('body').removeClass('mobile-nav-active');
          $('.mobile-nav-toggle i').toggleClass('icofont-navigation-menu icofont-close');
          $('.mobile-nav-overly').fadeOut();
        }

        return false;

      }
    }
  });

  // Activate/show sections on load with hash links
  if (window.location.hash) {
    var initial_nav = window.location.hash;
    if ($(initial_nav).length) {
      $('#header').addClass('header-top');
      $('.nav-menu .active, .mobile-nav .active').removeClass('active');
      $('.nav-menu, .mobile-nav').find('a[href="' + initial_nav + '"]').parent('li').addClass('active');
      setTimeout(function () {
        $("section").removeClass('section-show');
        $(initial_nav).addClass('section-show');
      }, 350);
    }
  }

  // Mobile Navigation
  if ($('.nav-menu').length) {
    var $mobile_nav = $('.nav-menu').clone().prop({
      class: 'mobile-nav d-lg-none'
    });
    $('body').append($mobile_nav);
    $('body').prepend('<button type="button" class="mobile-nav-toggle d-lg-none"><i class="icofont-navigation-menu"></i></button>');
    $('body').append('<div class="mobile-nav-overly"></div>');

    $(document).on('click', '.mobile-nav-toggle', function (e) {
      $('body').toggleClass('mobile-nav-active');
      $('.mobile-nav-toggle i').toggleClass('icofont-navigation-menu icofont-close');
      $('.mobile-nav-overly').toggle();
    });

    $(document).click(function (e) {
      var container = $(".mobile-nav, .mobile-nav-toggle");
      if (!container.is(e.target) && container.has(e.target).length === 0) {
        if ($('body').hasClass('mobile-nav-active')) {
          $('body').removeClass('mobile-nav-active');
          $('.mobile-nav-toggle i').toggleClass('icofont-navigation-menu icofont-close');
          $('.mobile-nav-overly').fadeOut();
        }
      }
    });
  } else if ($(".mobile-nav, .mobile-nav-toggle").length) {
    $(".mobile-nav, .mobile-nav-toggle").hide();
  }

})(jQuery);