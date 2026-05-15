import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './register.component.html'
})
export class RegisterComponent {

  username = '';
  password = '';

  constructor(
    private api: ApiService,
    private router: Router
  ) {}

  register() {

    this.api.register({
      username: this.username,
      password: this.password
    }).subscribe(() => {

      this.router.navigate(['/login']);

    });

  }
}